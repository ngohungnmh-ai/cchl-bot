# 🌿 CCHL Store Inspector Bot — Hướng dẫn cài đặt

Bot tự động đánh giá ảnh vệ sinh & setup cửa hàng Cỏ Cây Hoa Lá qua Telegram.

---

## Bước 1 — Tạo Telegram Bot

1. Mở Telegram, tìm **@BotFather**
2. Gửi lệnh `/newbot`
3. Đặt tên bot: ví dụ `CCHL Store Inspector`
4. Đặt username: ví dụ `cchl_store_bot`
5. BotFather sẽ trả về **TOKEN** — lưu lại, dùng ở bước 3

---

## Bước 2 — Lấy Anthropic API Key

1. Truy cập **console.anthropic.com**
2. Đăng nhập / tạo tài khoản
3. Vào **API Keys** → **Create Key**
4. Lưu key lại (chỉ hiện 1 lần)

---

## Bước 3 — Lấy Group ID của Telegram

1. Thêm bot **@userinfobot** vào group Telegram của bạn
2. Gõ `/start` trong group
3. Bot sẽ trả về thông tin group, lưu lại **Group ID** (số âm, VD: `-1001234567890`)
4. Xóa @userinfobot khỏi group sau khi lấy ID

---

## Bước 4 — Cài đặt & chạy bot

### Cách A: Chạy thẳng bằng Python (đơn giản)

```bash
# Yêu cầu: Python 3.10+

# 1. Cài thư viện
pip install -r requirements.txt

# 2. Tạo file .env
cp .env.example .env

# 3. Mở file .env và điền thông tin
nano .env
# Điền: TELEGRAM_TOKEN, ANTHROPIC_API_KEY, ALLOWED_GROUP_ID

# 4. Chạy bot
python src/bot.py
```

### Cách B: Chạy bằng Docker (khuyến nghị — chạy 24/7)

```bash
# Yêu cầu: Docker + Docker Compose đã cài

# 1. Tạo file .env
cp .env.example .env
nano .env   # điền thông tin

# 2. Build và chạy
docker-compose up -d

# 3. Xem logs
docker-compose logs -f

# 4. Dừng bot
docker-compose down
```

---

## Bước 5 — Thêm bot vào group Telegram

1. Vào group Telegram báo cáo vệ sinh
2. Thêm bot vào group (tìm theo username đã đặt ở Bước 1)
3. **Cấp quyền cho bot**: vào Settings → Administrators → Add Admin → chọn bot → bật quyền **Read Messages**
4. Gõ `/start` để kiểm tra bot phản hồi

---

## Cách dùng hàng ngày

| Ai | Làm gì |
|---|---|
| Nhân sự | Chụp ảnh từng khu → gửi vào group Telegram |
| Bot | Tự động phân tích → trả kết quả trong ~15 giây |
| Quản lý | Đọc báo cáo trong group, không cần làm thêm gì |

---

## Cấu trúc thư mục

```
cchl-bot/
├── src/
│   └── bot.py          # Code chính
├── logs/               # File log tự động tạo
├── .env.example        # Mẫu biến môi trường
├── .env                # Biến môi trường thực (KHÔNG commit lên git)
├── requirements.txt    # Thư viện Python
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Xử lý sự cố thường gặp

**Bot không phản hồi ảnh**
→ Kiểm tra bot đã được thêm vào group và có quyền đọc tin nhắn

**Lỗi "Unauthorized"**
→ TELEGRAM_TOKEN sai, kiểm tra lại

**Lỗi "API Error 401"**
→ ANTHROPIC_API_KEY sai hoặc hết credit, kiểm tra tại console.anthropic.com

**Bot phản hồi ở group khác**
→ Điền ALLOWED_GROUP_ID để giới hạn chỉ 1 group

---

## Chi phí ước tính

- Anthropic API: ~$0.003–0.005 / ảnh (Claude Sonnet)
- Nếu mỗi ngày gửi 10 ảnh → khoảng **$1–1.5 / tháng**
- Server chạy bot: VPS rẻ nhất (~$5/tháng) hoặc máy tính văn phòng bật 24/7
