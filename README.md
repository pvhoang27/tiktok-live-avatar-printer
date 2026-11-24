# 🖨️ TikTok LIVE – Máy in Avatar

Người xem tặng quà trên TikTok LIVE → máy in trên màn hình **in avatar + tên** của họ ra giấy.
Khung dọc **9:16 (1080×1920)** cho OBS / TikTok LIVE Studio.

| Quà | Hành động |
|---|---|
| 🌹 ≥ 1 xu (Hoa hồng) | **Print**: in thẻ nhỏ |
| 🍩 ≥ 30 xu (Bánh vòng) | **Big**: in thẻ to + pháo giấy |
| 💎 ≥ 100 xu | **Legendary VIPP**: banner tên toàn màn hình, thẻ viền vàng, nhạc |

Ngoài ra còn có: hàng chờ in, bảng vàng top 5 người tặng, thông báo follow/quà, và âm thanh máy in (tạo bằng WebAudio, không cần file âm thanh).

## Cách hoạt động

```
TikTok LIVE ──(TikTokLive, API không chính thức)──► server.py ──WebSocket──► overlay (OBS Browser Source)
                                                     ▲
                       panel /panel, TikFinity, Streamer.bot ── POST /api/gift
```

TikTok **không có API chính thức** cho quà trong live. Project này dùng thư viện
[TikTokLive](https://github.com/isaackogan/TikTokLive): chỉ cần username, không cần đăng nhập.
Nếu TikTok đổi hệ thống và thư viện bị hỏng, chạy `uv lock --upgrade && uv sync` để cập nhật.
Hoặc dùng TikFinity / Streamer.bot gọi `POST /api/gift` (xem bên dưới).

## Chạy

Cần cài [uv](https://docs.astral.sh/uv/).

```bash
uv sync                          # cài thư viện
uv run server.py --demo          # chạy thử, không cần live (tự sinh quà giả)
uv run server.py                 # kết nối live thật (username trong config.json)
uv run server.py --user @abc     # ghi đè username
```

- **Overlay**: http://localhost:8765/
- **Bảng điều khiển / tặng quà thử**: http://localhost:8765/panel

> Script cần kết nối **khi bạn đang live**. Nếu chưa live, nó tự thử lại sau mỗi 20 giây.
> Muốn test với live thật trước? Đặt `--user` là một kênh bất kỳ đang live.

## Đưa lên live

1. **OBS** (hoặc TikTok LIVE Studio): Thêm nguồn **Browser Source**
   - URL: `http://localhost:8765/`
   - Width `1080`, Height `1920`
   - Tick **Control audio via OBS** nếu muốn phát tiếng máy in
2. Canvas OBS đặt **1080×1920** (khung dọc).
3. Phát live:
   - **TikTok LIVE Studio**: thêm overlay như một nguồn trong Studio.
   - **OBS**: cần **stream key** của TikTok. Chỉ tài khoản đủ điều kiện mới có key.
4. Chạy `uv run server.py` → panel báo `connected` là xong.

## Tuỳ chỉnh (`config.json`)

| Khoá | Ý nghĩa |
|---|---|
| `tiktok_username` | kênh của bạn |
| `brand.title` / `brand.subtitle` | chữ logo ở nửa dưới |
| `rules` | ngưỡng xu → hành động (`print` / `big` / `legendary`), emoji và nhãn hiển thị trong menu |
| `gift_overrides` | ép một quà theo **tên tiếng Anh** (vd `"Rose": "print"`) sang hành động khác |
| `max_copies_per_event` | tặng combo x20 thì in tối đa mấy bản |
| `print_seconds` | thời gian in mỗi loại |
| `sound` | bật/tắt âm thanh |

**Video nền nửa dưới:** bỏ file `overlay/media/bg.mp4` vào thư mục đó (vd video lửa trại). Không có file thì dùng lửa CSS có sẵn.

## Gọi từ ngoài (TikFinity, Streamer.bot, curl)

```bash
curl -X POST http://localhost:8765/api/gift -H 'Content-Type: application/json' \
  -d '{"user":"Cintra","gift":"Rose","coins":1,"count":1,"avatar":"https://...tiktokcdn.com/..."}'
curl -X POST http://localhost:8765/api/clear          # xoá giấy + hàng chờ
curl -X POST "http://localhost:8765/api/clear?board=1" # reset bảng vàng
```

## Cấu trúc

```
server.py          # aiohttp: nghe TikTok, map quà → lệnh in, WebSocket, proxy ảnh avatar
config.json        # luật quà, brand, thời gian in
overlay/index.html # overlay 9:16
overlay/style.css
overlay/app.js     # hàng đợi + animation in + hiệu ứng + âm thanh
overlay/panel.html # bảng điều khiển / test
```
