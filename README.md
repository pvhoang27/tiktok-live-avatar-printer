# 🖨️ TikTok LIVE – Máy in Avatar

Người xem tặng quà trong buổi live → trên màn hình, máy in **in avatar + tên** của họ ra giấy.
Màn hình dọc **9:16 (1080×1920)**, dùng với **OBS** hoặc **TikTok LIVE Studio**.

| Quà | Kết quả trên màn hình |
|---|---|
| 🌹 từ 1 xu (Hoa hồng…) | **Print**: in thẻ nhỏ |
| 🍩 từ 30 xu (Bánh vòng…) | **Big**: in thẻ to + pháo giấy |
| 💎 từ 100 xu | **Legendary VIPP**: tên hiện to toàn màn hình + thẻ viền vàng + nhạc |

Ngoài ra có: hàng chờ in (nhiều người tặng cùng lúc vẫn in lần lượt, không sót ai), **bảng vàng top 5**, thông báo khi có người follow hoặc tặng quà, và tiếng máy in.

> ⚠️ Không cần tài khoản developer hay API key của TikTok, **chỉ cần username kênh**.
> Dự án dùng thư viện **không chính thức** [TikTokLive](https://github.com/isaackogan/TikTokLive) để đọc quà trong live, nên có thể tạm hỏng khi TikTok thay đổi hệ thống (xem mục [Xử lý sự cố](#-xử-lý-sự-cố)).

---

## 📋 Mục lục

1. [Chuẩn bị](#1-chuẩn-bị)
2. [Tải code về](#2-tải-code-về)
3. [Cài đặt](#3-cài-đặt)
4. [Chạy thử (không cần live)](#4-chạy-thử-không-cần-live)
5. [Cấu hình kênh của bạn](#5-cấu-hình-kênh-của-bạn)
6. [Gắn vào OBS / TikTok LIVE Studio](#6-gắn-vào-obs--tiktok-live-studio)
7. [Lên live](#7-lên-live)
8. [Tuỳ chỉnh](#8-tuỳ-chỉnh)
9. [Xử lý sự cố](#-xử-lý-sự-cố)

---

## 1. Chuẩn bị

Bạn cần có:

| Thứ cần có | Để làm gì |
|---|---|
| **Tài khoản TikTok live được từ máy tính** | Cần **TikTok LIVE Studio** (Windows/Mac) **hoặc** **stream key** để dùng OBS. Kiểm tra tại [tiktok.com/live/producer](https://www.tiktok.com/live/producer): nếu thấy *Server URL* và *Stream Key* là dùng OBS được. |
| **Bật nhận quà LIVE** | Để người xem tặng quà được (tài khoản phải đủ điều kiện, thường là từ 18 tuổi) |
| [Git](https://git-scm.com/downloads) | Tải code về |
| [uv](https://docs.astral.sh/uv/) | Cài Python + thư viện bằng 1 lệnh |
| [OBS Studio](https://obsproject.com/) (khuyên dùng) | Ghép màn hình máy in vào live |

**Cài uv** (chỉ làm 1 lần):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Cài xong thì **đóng terminal và mở lại**, rồi gõ `uv --version` để kiểm tra.
Không cần cài Python riêng, uv tự tải về.

---

## 2. Tải code về

```bash
git clone https://github.com/pvhoang27/tiktok-live-avatar-printer.git
cd tiktok-live-avatar-printer
```

> Không dùng Git? Trên trang GitHub bấm **Code → Download ZIP**, giải nén, rồi mở terminal trong thư mục vừa giải nén.

---

## 3. Cài đặt

```bash
uv sync
```

Lệnh này tự tải Python và các thư viện cần thiết vào thư mục `.venv`. Chỉ cần chạy lại khi bạn `git pull` bản mới.

---

## 4. Chạy thử (không cần live)

```bash
uv run server.py --demo
```

Terminal sẽ hiện:

```
  Overlay (OBS): http://localhost:8765/
  Panel test   : http://localhost:8765/panel
  Chế độ       : demo
```

Mở 2 link này trên trình duyệt:

- **http://localhost:8765/**: màn hình máy in (cái người xem sẽ thấy). Ở chế độ demo, cứ vài giây lại có quà giả để bạn xem thử.
- **http://localhost:8765/panel**: bảng điều khiển. Gõ tên, bấm **Print / Big / Legendary** để tặng quà thử.

Thấy máy in chạy là cài đặt đã thành công. Bấm **Ctrl + C** trong terminal để tắt.

---

## 5. Cấu hình kênh của bạn

Mở file **`config.json`** và sửa username thành kênh của bạn:

```json
"tiktok_username": "@ten_kenh_cua_ban",
```

Có thể ghi `@abc`, `abc` hoặc dán cả link `https://www.tiktok.com/@abc/live`, cách nào cũng được.
Bạn **không cần** đổi link mỗi lần live, chương trình tự tìm phiên live mới.

Đổi luôn tên hiển thị dưới logo:

```json
"brand": {
  "title": "SHAN",
  "subtitle": "Tặng quà để được in lên giấy!"
},
```

---

## 6. Gắn vào OBS / TikTok LIVE Studio

### Với OBS

1. **Settings → Video**
   - Base (Canvas) Resolution: `1080x1920`
   - Output (Scaled) Resolution: `1080x1920`
2. Trong khung **Sources**, bấm **+ → Browser**, đặt tên `May in`, rồi điền:
   - URL: `http://localhost:8765/`
   - Width: `1080`, Height: `1920`
   - ✅ Tick **Control audio via OBS** (để phát tiếng máy in lên live)
3. **Settings → Stream**
   - Service: **Custom…**
   - Server và Stream Key: lấy từ [tiktok.com/live/producer](https://www.tiktok.com/live/producer)

### Với TikTok LIVE Studio (Windows / Mac)

LIVE Studio **không nhận link `localhost`**, nên hãy dùng một trong 2 cách sau.

**Cách 1: Quay cửa sổ (đơn giản nhất)**

1. Mở `http://localhost:8765/` bằng Chrome.
   Mẹo: chạy `chrome --app=http://localhost:8765/ --window-size=540,960` để có cửa sổ gọn, không có thanh địa chỉ.
2. Trong LIVE Studio thêm nguồn **Window Capture / Quay cửa sổ**, rồi chọn cửa sổ Chrome đó.
3. Không thu nhỏ (minimize) cửa sổ Chrome trong lúc live, vì như vậy nó sẽ ngừng vẽ.

**Cách 2: OBS Virtual Camera (nét nhất, đầy đủ hiệu ứng)**

1. Dựng cảnh trong OBS như phần **Với OBS** ở trên (bỏ qua bước Settings → Stream).
2. Trong OBS bấm **Start Virtual Camera**.
3. Trong LIVE Studio thêm nguồn **Camera**, rồi chọn **OBS Virtual Camera**.

### ❓ Vì sao TikTok không nhận `localhost`?

`localhost` có nghĩa là **"chính máy này"**, nên chỉ phần mềm chạy **trên máy bạn** (Chrome, OBS) mới mở được link đó.
Nếu dán `localhost` vào trang web hay ô link của TikTok, server TikTok sẽ đi tìm trên **máy của TikTok**, nên không thấy gì.

TikTok **không cần** link này. Luồng đúng là:

```
localhost:8765 ──► OBS / LIVE Studio quay lại thành video ──► gửi VIDEO lên TikTok
```

---

## 7. Lên live

Mỗi lần live bạn chỉ cần:

```bash
uv run server.py
```

1. Bật live (OBS bấm **Start Streaming**, hoặc **Go LIVE** trong LIVE Studio).
2. Mở **http://localhost:8765/panel** (có thể mở trên điện thoại hoặc màn hình phụ). Khi thấy chấm xanh **connected** là đã nối được với live.
3. Nhờ bạn bè, hoặc dùng một tài khoản phụ, **tặng 1 bông hồng** để kiểm tra. (Bạn không tự tặng cho chính mình được.)

> Chạy server **trước** khi bật live cũng được: nó báo `offline` rồi tự thử lại mỗi 20 giây, khi bạn lên sóng sẽ tự kết nối.
>
> Muốn thử nghe một kênh khác **đang live** mà không sửa config:
> `uv run server.py --user @kenh_khac`

**Trong khi live phải để 3 thứ cùng chạy:** OBS/LIVE Studio, cửa sổ terminal đang chạy `server.py`, và nguồn Browser trong OBS.
Nếu tắt terminal thì live vẫn lên hình nhưng **máy in sẽ đứng im**.

---

## 8. Tuỳ chỉnh

### Mức quà (`config.json`)

```json
"rules": [
  { "min_coins": 1,   "action": "print",     "label": "Print",          "emoji": "🌹", "hint": "1 xu" },
  { "min_coins": 30,  "action": "big",       "label": "Big",            "emoji": "🍩", "hint": "30 xu" },
  { "min_coins": 100, "action": "legendary", "label": "Legendary VIPP", "emoji": "💎", "hint": "100 xu" }
],
```

Chương trình xét quà theo **số xu**: quà có giá từ `min_coins` trở lên thì chạy hành động tương ứng. Cách này áp dụng được cho mọi loại quà, kể cả quà mới.

| Khoá | Ý nghĩa |
|---|---|
| `gift_overrides` | Gán cứng một quà (theo **tên tiếng Anh**, vd `"Rose"`) vào một hành động |
| `max_copies_per_event` | Người xem tặng combo x20 thì in tối đa mấy bản (mặc định 5) |
| `max_queue` | Số lệnh in tối đa được xếp hàng chờ |
| `print_seconds` | Thời gian in (giây) của từng loại |
| `sound` | `true` / `false`: bật hoặc tắt tiếng máy in |
| `port` | Cổng chạy server (mặc định 8765) |

Sửa xong thì tắt server (Ctrl + C) rồi chạy lại. Trong OBS, chuột phải vào nguồn Browser → **Refresh**.

### Video nền

Bỏ một file video tên **`bg.mp4`** vào thư mục `overlay/media/` (ví dụ video lửa trại, logo động…). Video sẽ chạy lặp ở nửa dưới màn hình.
Nếu không có file thì chương trình dùng hiệu ứng lửa có sẵn.

### Giao diện

- Màu, kích thước, bố cục: `overlay/style.css`
- Hiệu ứng, âm thanh, tốc độ đầu in: `overlay/app.js`

---

## 🔌 Gửi quà từ công cụ khác (TikFinity, Streamer.bot…)

Nếu kết nối có sẵn bị hỏng, bạn có thể để **TikFinity** hoặc **Streamer.bot** gửi sự kiện quà vào server qua HTTP:

```bash
curl -X POST http://localhost:8765/api/gift \
  -H "Content-Type: application/json" \
  -d '{"user":"Cintra","gift":"Rose","coins":1,"count":1,"avatar":"https://link-anh-avatar"}'
```

```bash
curl -X POST http://localhost:8765/api/clear            # xoá giấy + hàng chờ
curl -X POST "http://localhost:8765/api/clear?board=1"  # reset bảng vàng
```

---

## 🛠 Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| `uv: command not found` | Đóng terminal, mở lại. Nếu vẫn lỗi thì cài lại uv (mục 1). |
| Panel báo **offline** | Kênh chưa live, hoặc sai username trong `config.json`. Server sẽ tự thử lại. |
| Panel báo **error** liên tục | Có thể TikTok vừa thay đổi hệ thống. Chạy `uv lock --upgrade && uv sync` để cập nhật thư viện, rồi chạy lại. |
| Panel báo connected nhưng tặng quà không in | Xem terminal có dòng `Quà: ... -> print` không. Nếu có mà OBS không chạy thì **Refresh** nguồn Browser. |
| TikTok / LIVE Studio báo link `localhost` không hợp lệ | Bình thường: TikTok không mở được link trên máy bạn. Dùng OBS Browser Source, hoặc quay cửa sổ / Virtual Camera (xem mục 6). |
| Nguồn Browser trong OBS trắng xoá | Kiểm tra `uv run server.py` **đang chạy**. Thử URL `http://127.0.0.1:8765/` thay cho `localhost`. |
| OBS không có tiếng máy in | Tick **Control audio via OBS** trong nguồn Browser. |
| Màn hình bị lệch hoặc thừa viền | Canvas OBS và nguồn Browser đều phải là **1080×1920**. |
| Báo cổng 8765 đang bận | Có server cũ chưa tắt, hoặc chạy cổng khác: `uv run server.py --port 9000` (nhớ đổi URL trong OBS). |
| Bị giới hạn kết nối (rate limit) | Thư viện dùng server ký trung gian [Euler Stream](https://www.eulerstream.com/), bản miễn phí có giới hạn. Nếu cần có thể mua key và chạy `SIGN_API_KEY=key_cua_ban uv run server.py` (Windows: `$env:SIGN_API_KEY="key_cua_ban"; uv run server.py`). **Không** ghi key vào `config.json`. |

---

## ⚙️ Cách hoạt động

```
Người xem tặng 🌹 ──► TikTok (trừ xu người xem, cộng Kim cương cho bạn)
                          │  phát sự kiện "Cintra tặng Rose"
                          ▼
                     server.py  ── nghe live như một người xem (không đăng nhập)
                          │  tra config.json: 1 xu → print
                          ▼
                  overlay (trang web) ── xếp hàng → animation in avatar
                          │
                          ▼
                  OBS / LIVE Studio ── phát lên TikTok → người xem thấy tên mình được in
```

- **Tiền không đi qua chương trình này.** TikTok tự xử lý, chương trình chỉ "nghe" để biết ai vừa tặng.
- Chương trình chỉ **đọc** những thông tin công khai mà người xem nào cũng thấy (tên, avatar, quà). Nó không đăng nhập và không gửi gì lên tài khoản của bạn.

```
server.py            nghe TikTok, đổi quà → lệnh in, gửi qua WebSocket
config.json          username, mức quà, brand, thời gian in
overlay/index.html   màn hình 9:16 (đưa vào OBS)
overlay/style.css    giao diện
overlay/app.js       hàng chờ + animation in + hiệu ứng + âm thanh
overlay/panel.html   bảng điều khiển / tặng quà thử
```

---

Dự án dùng thư viện không chính thức và **không liên kết với TikTok/ByteDance**. Hãy tuân thủ [nguyên tắc LIVE của TikTok](https://www.tiktok.com/community-guidelines) khi phát sóng.
