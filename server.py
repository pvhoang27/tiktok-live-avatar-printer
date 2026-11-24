"""
TikTok LIVE "máy in avatar".

- Nghe sự kiện tặng quà từ TikTok LIVE (thư viện không chính thức TikTokLive)
- Đổi quà -> lệnh in (print / big / legendary) theo config.json
- Đẩy lệnh in tới overlay (overlay/index.html) qua WebSocket
- Overlay được thêm vào OBS / TikTok LIVE Studio dưới dạng Browser Source

Chạy:
    uv run server.py                 # kết nối live thật (username trong config.json)
    uv run server.py --demo          # không cần live, tự sinh quà giả để test
    uv run server.py --user @abc     # ghi đè username
Mở:
    http://localhost:8765/           -> overlay (đưa vào OBS)
    http://localhost:8765/panel      -> bảng điều khiển, bấm thử quà
"""

from __future__ import annotations

import argparse
import asyncio
import itertools
import json
import logging
import pathlib
import random
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientTimeout, WSMsgType, web

ROOT = pathlib.Path(__file__).resolve().parent
OVERLAY = ROOT / "overlay"
CONFIG_PATH = ROOT / "config.json"

log = logging.getLogger("printer")

# Chỉ proxy ảnh từ CDN của TikTok (không cho thành open proxy)
ALLOWED_IMG_HOSTS = ("tiktokcdn.com", "tiktokcdn-us.com", "tiktokcdn-eu.com",
                     "ibyteimg.com", "byteimg.com", "muscdn.com")

_job_ids = itertools.count(1)


# ----------------------------------------------------------------- config ---

def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text("utf-8"))


def resolve_action(cfg: dict, gift_name: str, coins: int) -> str | None:
    """Quà -> hành động. Ưu tiên gift_overrides theo tên, sau đó theo số xu."""
    for name, action in cfg.get("gift_overrides", {}).items():
        if name.lower() == (gift_name or "").lower():
            return action
    best = None
    for rule in sorted(cfg["rules"], key=lambda r: r["min_coins"]):
        if coins >= rule["min_coins"]:
            best = rule["action"]
    return best


def public_config(cfg: dict) -> dict:
    return {k: cfg[k] for k in ("brand", "rules", "print_seconds", "sound", "max_queue") if k in cfg}


# -------------------------------------------------------------------- hub ---

class Hub:
    """Giữ danh sách client WebSocket (overlay + panel) và phát sự kiện."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.clients: set[web.WebSocketResponse] = set()
        self.status = {"state": "idle", "detail": "", "user": ""}
        self.board: dict[str, dict] = {}   # bảng vàng: tên -> {coins, avatar}

    def top(self, n: int = 5) -> list[dict]:
        rows = sorted(self.board.items(), key=lambda kv: -kv[1]["coins"])[:n]
        return [{"user": k, **v} for k, v in rows]

    async def send(self, msg: dict) -> None:
        data = json.dumps(msg, ensure_ascii=False)
        for ws in list(self.clients):
            try:
                await ws.send_str(data)
            except Exception:
                self.clients.discard(ws)

    async def set_status(self, state: str, detail: str = "") -> None:
        self.status.update(state=state, detail=detail)
        log.info("TikTok: %s %s", state, detail)
        await self.send({"type": "status", **self.status})

    async def gift(self, *, user: str, avatar: str, gift: str, coins: int,
                   count: int = 1, gift_image: str = "") -> None:
        action = resolve_action(self.cfg, gift, coins)
        log.info("Quà: %s tặng %s x%d (%d xu) -> %s", user, gift, count, coins, action)
        await self.send({"type": "feed", "user": user, "gift": gift,
                         "count": count, "coins": coins, "action": action})
        if not action:
            return
        row = self.board.setdefault(user, {"coins": 0, "avatar": ""})
        row["coins"] += coins * count
        row["avatar"] = proxied(avatar) or row["avatar"]
        await self.send({"type": "board", "top": self.top()})
        copies = max(1, min(count, int(self.cfg.get("max_copies_per_event", 5))))
        for _ in range(copies):
            await self.send({
                "type": "job",
                "id": next(_job_ids),
                "action": action,
                "user": user,
                "avatar": proxied(avatar),
                "gift": gift,
                "gift_image": proxied(gift_image),
                "coins": coins,
            })


def proxied(url: str) -> str:
    if not url or not url.startswith("http"):
        return url or ""
    from urllib.parse import quote
    return "/img?u=" + quote(url, safe="")


def first_url(image) -> str:
    try:
        urls = image.url_list
        return urls[0] if urls else ""
    except Exception:
        return ""


# ----------------------------------------------------------------- TikTok ---

async def run_tiktok(hub: Hub, username: str) -> None:
    from TikTokLive import TikTokLiveClient
    from TikTokLive.client.errors import UserOfflineError
    from TikTokLive.events import (CommentEvent, ConnectEvent, DisconnectEvent,
                                   FollowEvent, GiftEvent, LiveEndEvent)

    hub.status["user"] = username
    while True:
        client = TikTokLiveClient(unique_id=username)

        @client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            await hub.set_status("connected", f"room {client.room_id}")

        @client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            # Quà combo (vd hoa hồng bấm liên tục) bắn nhiều event:
            # chỉ xử lý khi combo kết thúc, repeat_count = tổng số.
            if event.streaking:
                return
            u, g = event.user, event.gift
            if g is None or u is None:
                return
            await hub.gift(
                user=u.nickname or u.unique_id or "Ẩn danh",
                avatar=first_url(u.avatar_medium) or first_url(u.avatar_thumb),
                gift=g.name,
                coins=int(g.diamond_count or 0),
                count=int(event.repeat_count or 1),
                gift_image=first_url(g.image),
            )

        @client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            await hub.send({"type": "comment", "user": event.user.nickname,
                            "text": event.comment})

        @client.on(FollowEvent)
        async def on_follow(event: FollowEvent):
            await hub.send({"type": "feed", "user": event.user.nickname,
                            "gift": "follow", "count": 1, "coins": 0, "action": None})

        @client.on(LiveEndEvent)
        async def on_end(event: LiveEndEvent):
            await hub.set_status("ended", "live đã kết thúc")

        @client.on(DisconnectEvent)
        async def on_disconnect(event: DisconnectEvent):
            await hub.set_status("disconnected")

        try:
            await hub.set_status("connecting", username)
            await client.connect()
        except UserOfflineError:
            await hub.set_status("offline", f"{username} chưa live, thử lại sau 20s")
        except asyncio.CancelledError:
            raise
        except Exception as ex:  # TikTok đổi API, captcha, mạng...
            await hub.set_status("error", f"{type(ex).__name__}: {ex}")
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass
        await asyncio.sleep(20)


# ------------------------------------------------------------------- demo ---

DEMO_NAMES = ["Cintra", "tami", "chekyy8", "mati", "O$car", "Guddu", "iki",
              "Isamar", "Boss Rc jr.", "Ysabelly", "EDWIN", "Amairani"]


def demo_avatar(name: str) -> str:
    return "/demo-avatar/" + "".join(c for c in name if c.isalnum())[:12]


async def run_demo(hub: Hub) -> None:
    await hub.set_status("demo", "đang tạo quà giả")
    gifts = [("Rose", 1)] * 6 + [("Doughnut", 30)] * 2 + [("Hand Hearts", 100)]
    while True:
        await asyncio.sleep(random.uniform(3, 7))
        name = random.choice(DEMO_NAMES)
        gift, coins = random.choice(gifts)
        await hub.gift(user=name, avatar=demo_avatar(name), gift=gift, coins=coins)


# -------------------------------------------------------------------- web ---

async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    hub: Hub = request.app["hub"]
    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)
    hub.clients.add(ws)
    await ws.send_str(json.dumps({"type": "config", **public_config(hub.cfg)}, ensure_ascii=False))
    await ws.send_str(json.dumps({"type": "status", **hub.status}, ensure_ascii=False))
    await ws.send_str(json.dumps({"type": "board", "top": hub.top()}, ensure_ascii=False))
    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue
            try:
                data = json.loads(msg.data)
            except ValueError:
                continue
            # overlay báo số lệnh đang chờ -> chuyển tiếp cho panel
            if data.get("type") == "queue":
                await hub.send({"type": "queue", "size": int(data.get("size", 0))})
    finally:
        hub.clients.discard(ws)
    return ws


async def api_test_gift(request: web.Request) -> web.Response:
    hub: Hub = request.app["hub"]
    body = await request.json()
    name = str(body.get("user") or random.choice(DEMO_NAMES))[:40]
    await hub.gift(user=name, avatar=body.get("avatar") or demo_avatar(name),
                   gift=str(body.get("gift", "Rose")), coins=int(body.get("coins", 1)),
                   count=int(body.get("count", 1)))
    return web.json_response({"ok": True})


async def api_clear(request: web.Request) -> web.Response:
    hub: Hub = request.app["hub"]
    if request.query.get("board"):
        hub.board.clear()
        await hub.send({"type": "board", "top": []})
    await hub.send({"type": "clear"})
    return web.json_response({"ok": True})


async def img_proxy(request: web.Request) -> web.Response:
    url = request.query.get("u", "")
    host = urlparse(url).hostname or ""
    if urlparse(url).scheme != "https" or not host.endswith(ALLOWED_IMG_HOSTS):
        raise web.HTTPForbidden()
    cache: dict = request.app["img_cache"]
    if url not in cache:
        async with request.app["http"].get(url, headers={"Referer": "https://www.tiktok.com/"}) as r:
            if r.status != 200:
                raise web.HTTPNotFound()
            cache[url] = (await r.read(), r.headers.get("Content-Type", "image/jpeg"))
        if len(cache) > 500:
            cache.pop(next(iter(cache)))
    data, ctype = cache[url]
    return web.Response(body=data, content_type=ctype.split(";")[0],
                        headers={"Cache-Control": "max-age=3600"})


async def demo_avatar_svg(request: web.Request) -> web.Response:
    """Avatar giả (chữ cái đầu) để test mà không cần mạng."""
    name = request.match_info["name"] or "?"
    hue = sum(map(ord, name)) * 47 % 360
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="hsl({hue},70%,62%)"/><stop offset="1" stop-color="hsl({(hue+60)%360},70%,40%)"/>
</linearGradient></defs><rect width="200" height="200" fill="url(#g)"/>
<circle cx="100" cy="78" r="38" fill="rgba(255,255,255,.85)"/>
<path d="M30 200c6-50 36-74 70-74s64 24 70 74z" fill="rgba(255,255,255,.85)"/>
<text x="100" y="94" font-family="sans-serif" font-size="44" font-weight="700" text-anchor="middle"
fill="hsl({hue},60%,35%)">{name[0].upper()}</text></svg>"""
    return web.Response(text=svg, content_type="image/svg+xml")


async def page(request: web.Request) -> web.FileResponse:
    return web.FileResponse(OVERLAY / request.match_info.get("file", "index.html"))


def build_app(cfg: dict, mode: str, username: str) -> web.Application:
    app = web.Application()
    hub = Hub(cfg)
    app["hub"] = hub
    app["img_cache"] = {}

    async def on_startup(app: web.Application):
        app["http"] = ClientSession(timeout=ClientTimeout(total=10))
        coro = run_demo(hub) if mode == "demo" else run_tiktok(hub, username)
        app["bg"] = asyncio.create_task(coro)

    async def on_cleanup(app: web.Application):
        app["bg"].cancel()
        await app["http"].close()

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.router.add_get("/", page)
    app.router.add_get("/panel", lambda r: web.FileResponse(OVERLAY / "panel.html"))
    app.router.add_get("/ws", ws_handler)
    app.router.add_post("/api/gift", api_test_gift)
    app.router.add_post("/api/clear", api_clear)
    app.router.add_get("/img", img_proxy)
    app.router.add_get("/demo-avatar/{name:.*}", demo_avatar_svg)
    app.router.add_static("/static", OVERLAY)
    return app


def main() -> None:
    ap = argparse.ArgumentParser(description="TikTok LIVE avatar printer")
    ap.add_argument("--demo", action="store_true", help="không kết nối TikTok, tự sinh quà giả")
    ap.add_argument("--user", help="username TikTok (ghi đè config.json)")
    ap.add_argument("--port", type=int)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    cfg = load_config()
    username = args.user or cfg["tiktok_username"]
    port = args.port or cfg.get("port", 8765)
    mode = "demo" if args.demo else "live"

    print(f"\n  Overlay (OBS): http://localhost:{port}/")
    print(f"  Panel test   : http://localhost:{port}/panel")
    print(f"  Chế độ       : {mode}" + ("" if args.demo else f" ({username})") + "\n")
    web.run_app(build_app(cfg, mode, username), host="127.0.0.1", port=port, print=None)


if __name__ == "__main__":
    main()
