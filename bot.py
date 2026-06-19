"""
CCHL Store Inspection Bot - Tieng Viet co dau
"""

import os
import logging
import base64
import json
import re
from datetime import datetime
from io import BytesIO
from collections import defaultdict

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ALLOWED_GROUP_ID = int(os.environ.get("ALLOWED_GROUP_ID", "0") or "0")

pending_photos = defaultdict(lambda: {"photos": [], "sender": ""})

EVALUATION_PROMPT = """You are inspecting a Co Cay Hoa La (CCHL) store. Analyze this image.

Return ONLY valid JSON with Vietnamese text (with diacritics/tone marks):
{
  "khu_vuc": "HAIR or BODY or FACE or GIFT or WC or TONG THE or KHONG XAC DINH",
  "diem": 8,
  "dat_chuan": true,
  "loi_phat_hien": ["Mô tả lỗi bằng tiếng Việt có dấu"],
  "khuyen_nghi": ["Việc cần làm bằng tiếng Việt có dấu"]
}

Standards:
- HAIR: Kệ sạch, sản phẩm thẳng hàng, túi refill xanh trên cùng, biển HAIR rõ, nhãn giá đúng, đủ hàng
- BODY: Kệ sạch, sản phẩm đúng nhóm, túi refill cam đúng vị trí, đủ hàng
- FACE: Kệ sạch, nhóm đúng, nhãn Hàng Mới Về đúng chỗ, đủ hàng
- GIFT/COMBO: Hộp quà gọn, biển rõ, đủ hàng
- WC: Bồn cầu sạch, sàn khô, tường không mốc, thùng rác có túi
- TONG THE: Sàn sạch, cửa kính sạch, đèn đủ, TV bật, quầy thu ngân gọn

Write loi_phat_hien and khuyen_nghi in Vietnamese WITH tone marks. Max 2 items each. Keep short."""


async def analyze_image_with_claude(image_bytes: bytes) -> dict:
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
            {"type": "text", "text": EVALUATION_PROMPT}
        ]}]
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
    raw = resp.json()["content"][0]["text"].strip()
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    match = re.search(r'\{.*\}', clean, re.DOTALL)
    if match:
        clean = match.group(0)
    return json.loads(clean)


def format_summary_report(results: list, sender_name: str) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    total = len(results)
    dat_count = sum(1 for r in results if r.get("dat_chuan"))
    chua_dat = total - dat_count
    avg_score = round(sum(r.get("diem", 0) for r in results) / total, 1) if total else 0

    overall_emoji = "🟢" if avg_score >= 9 else ("🟡" if avg_score >= 7 else ("🟠" if avg_score >= 5 else "🔴"))
    overall_status = "ĐẠT CHUẨN ✅" if chua_dat == 0 else f"CÓ {chua_dat}/{total} KHU CHƯA ĐẠT ❌"

    lines = [
        "📋 *BÁO CÁO CỬA HÀNG CCHL*",
        f"👤 {sender_name}  |  🕐 {now}",
        f"{overall_emoji} Điểm TB: *{avg_score}/10*  —  {overall_status}",
        "",
        "*KẾT QUẢ TỪNG KHU:*",
    ]

    for r in results:
        khu = r.get("khu_vuc", "?")
        diem = r.get("diem", 0)
        dat = r.get("dat_chuan", False)
        icon = "✅" if dat else "❌"
        d_emoji = "🟢" if diem >= 9 else ("🟡" if diem >= 7 else ("🟠" if diem >= 5 else "🔴"))
        lines.append(f"{icon} {khu}  {d_emoji} {diem}/10")

    all_loi = []
    all_khuyen = []
    for r in results:
        khu = r.get("khu_vuc", "?")
        for loi in r.get("loi_phat_hien", []):
            if loi:
                all_loi.append(f"• [{khu}] {loi}")
        for k in r.get("khuyen_nghi", []):
            if k:
                all_khuyen.append(f"→ [{khu}] {k}")

    if all_loi:
        lines.append("")
        lines.append("⚠️ *LỖI PHÁT HIỆN:*")
        lines.extend(all_loi[:8])

    if all_khuyen:
        lines.append("")
        lines.append("🔧 *CẦN XỬ LÝ:*")
        lines.extend(all_khuyen[:8])

    lines.append("\n#CCHL #BaoCaoSang")
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌿 *CCHL Store Inspector Bot*\n\n"
        "1️⃣ Gửi album ảnh cửa hàng vào group\n"
        "2️⃣ Gõ /baocao → bot phân tích và trả báo cáo\n"
        "3️⃣ Gõ /reset để bắt đầu lại\n\n"
        "_Bot sẽ im lặng khi nhận ảnh — chỉ trả kết quả khi gõ /baocao_",
        parse_mode="Markdown"
    )

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    pending_photos[chat_id] = {"photos": [], "sender": ""}
    await update.message.reply_text("🔄 Đã xóa. Sẵn sàng nhận ảnh mới!")

async def baocao_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    data = pending_photos[chat_id]
    photos = data["photos"]
    sender = data["sender"]

    if not photos:
        await update.message.reply_text("⚠️ Chưa có ảnh nào. Gửi album ảnh cửa hàng trước rồi gõ /baocao.")
        return

    processing = await update.message.reply_text(f"⏳ Đang phân tích {len(photos)} ảnh, vui lòng chờ...")

    results = []
    for image_bytes in photos:
        try:
            result = await analyze_image_with_claude(image_bytes)
            results.append(result)
        except Exception as e:
            logger.error(f"Loi phan tich: {e}")

    if not results:
        await processing.edit_text("⚠️ Không phân tích được ảnh nào. Vui lòng thử lại.")
        return

    report = format_summary_report(results, sender)
    await processing.delete()
    await update.message.reply_text(report, parse_mode="Markdown")
    pending_photos[chat_id] = {"photos": [], "sender": ""}
    logger.info(f"Xuat bao cao: {len(results)} anh")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if ALLOWED_GROUP_ID and msg.chat_id != ALLOWED_GROUP_ID:
        return
    chat_id = msg.chat_id
    sender_name = msg.from_user.full_name or msg.from_user.username or "Không rõ"
    if not pending_photos[chat_id]["sender"]:
        pending_photos[chat_id]["sender"] = sender_name
    try:
        photo = msg.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        buf = BytesIO()
        await file.download_to_memory(buf)
        pending_photos[chat_id]["photos"].append(buf.getvalue())
        logger.info(f"Nhan anh #{len(pending_photos[chat_id]['photos'])} tu {sender_name}")
    except Exception as e:
        logger.error(f"Loi nhan anh: {e}")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("baocao", baocao_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    logger.info("Bot dang chay...")
    app.run_polling()

if __name__ == "__main__":
    main()
