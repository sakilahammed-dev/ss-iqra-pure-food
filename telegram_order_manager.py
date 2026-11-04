"""
=============================================================================
SS Iqra Pure Food - Telegram Order Notification & Steadfast Courier Pipeline
=============================================================================
Developed for: Sakil Ahammed (শাকিল আহাম্মেদ)
Founder: SS Iqra Pure Food (এস এস ইকরা পিওর ফুড)
Advisor: কলিজা (Kolija)

Key Highlights:
1. Real-time Telegram Order Slip Alert to @ssiqrapurefood_bot
2. One-click WhatsApp link & phone dialer integration
3. Standby Mode for manual Steadfast verification (Pilot Phase: 100% human-verified)
4. Automated logging to 02_Customer_Orders_Log.csv
5. Full Steadfast REST API integration ready to activate for Phase 2
=============================================================================
"""

import os
import sys
import json
import csv
import time
import urllib.request
import urllib.parse
from datetime import datetime

# Configure UTF-8 output for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ==========================================
# 1. CONFIGURATION & CREDENTIALS
# ==========================================
BOT_TOKEN = "8994135697:AAGIj-8CYdXsZnDp1XK3pK9ngE33wu27H74"
ADMIN_CHAT_ID = "8740322769"  # Sakil's Telegram ID

# Base Paths
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
ORDERS_CSV_PATH = os.path.join(WORKSPACE_DIR, "02_Customer_Orders_Log.csv")

# Steadfast Courier Configuration
# STANDBY_MODE = True: Provides copy-paste booking format & logs to CSV (Safest for starting)
# STANDBY_MODE = False: Directly calls Steadfast live REST API with API keys
STANDBY_MODE = True
STEADFAST_API_KEY = os.getenv("STEADFAST_API_KEY", "")
STEADFAST_SECRET_KEY = os.getenv("STEADFAST_SECRET_KEY", "")
STEADFAST_API_URL = "https://portal.steadfast.com.bd/api/v1/create_order"


# ==========================================
# 2. TELEGRAM API HELPER FUNCTIONS
# ==========================================
def send_telegram_request(endpoint: str, payload: dict) -> dict:
    """Send a POST request to Telegram Bot API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[Telegram API Error] {endpoint}: {e}")
        return {"ok": False, "error": str(e)}


def send_order_notification(order: dict) -> bool:
    """
    Format and send a rich Bengali order alert slip to Sakil's Telegram bot.
    Includes interactive inline buttons for WhatsApp and Steadfast booking slip.
    """
    invoice = order.get("invoice", f"SS-{int(time.time()) % 100000}")
    name = order.get("name", "গ্রাহকের নাম")
    phone = order.get("phone", "017XXXXXXXX")
    address = order.get("address", "ঠিকানা দেওয়া হয়নি")
    product = order.get("product", "১ কেজি মেগা ফ্যামিলি জার হানি-নাট")
    cod_amount = order.get("cod_amount", 890)
    note = order.get("note", "ডেলিভারির সময় চেক করে মূল্য পরিশোধ করবেন।")

    # Clean phone for WhatsApp URL
    clean_phone = phone.replace(" ", "").replace("-", "")
    if clean_phone.startswith("01"):
        wa_phone = f"88{clean_phone}"
    elif clean_phone.startswith("+8801"):
        wa_phone = clean_phone.replace("+", "")
    else:
        wa_phone = clean_phone

    text = (
        f"[ORDER ALERT] নতুন অর্ডারের নোটিফিকেশন (SS Iqra Pure Food)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*ইনভয়েস আইডি:* `#{invoice}`\n"
        f"*পণ্য:* {product}\n"
        f"*ক্যাশ অন ডেলিভারি বিল:* ৳{cod_amount}\n"
        f"*কাস্টমার:* {name}\n"
        f"*মোবাইল:* `{phone}`\n"
        f"*ঠিকানা:* {address}\n"
        f"*বিশেষ নোট:* {note}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*স্ট্যাটাস:* পেন্ডিং (কল কনফার্মেশন ও বুকিং)\n"
        f"*পরবর্তী পদক্ষেপ:* কাস্টমারকে কল দিয়ে অর্ডারটি চূড়ান্ত করুন।"
    )

    # Inline Keyboard with Actions
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "WhatsApp-এ চ্যাট করুন", "url": f"https://wa.me/{wa_phone}"}
            ],
            [
                {"text": "Steadfast বুকিং স্লিপ দেখুন", "callback_data": f"sf_view_{invoice}"},
                {"text": "অর্ডার কনফার্মড", "callback_data": f"sf_confirm_{invoice}"}
            ]
        ]
    }

    payload = {
        "chat_id": ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }

    resp = send_telegram_request("sendMessage", payload)
    if resp.get("ok"):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Order #{invoice} notification successfully sent to Telegram!")
        # Also log order into CSV
        log_order_to_csv(order)
        return True
    else:
        print(f"Failed to send order notification: {resp}")
        return False


# ==========================================
# 3. CSV LOGGING ENGINE
# ==========================================
def log_order_to_csv(order: dict):
    """
    Log or update the customer order in 02_Customer_Orders_Log.csv.
    """
    headers = [
        "তারিখ",
        "ইনভয়েস আইডি",
        "কাস্টমারের নাম",
        "মোবাইল নম্বর",
        "সম্পূর্ণ ডেলিভারি ঠিকানা",
        "অর্ডারকৃত পণ্য ও পরিমাণ",
        "মোট বিল (টাকা)",
        "কুরিয়ার স্ট্যাটাস",
        "Steadfast ট্র্যাকিং আইডি"
    ]

    date_str = datetime.now().strftime("%Y-%m-%d")
    invoice = order.get("invoice", f"SS-{int(time.time()) % 100000}")
    name = order.get("name", "")
    phone = order.get("phone", "")
    address = order.get("address", "")
    product = order.get("product", "১ কেজি হানি-নাট মেগা জার (১টি)")
    cod_amount = order.get("cod_amount", 890)
    status = order.get("status", "Pending Call Confirmation")
    tracking = order.get("tracking", "Pending")

    file_exists = os.path.isfile(ORDERS_CSV_PATH)
    
    rows = []
    updated = False
    if file_exists:
        try:
            with open(ORDERS_CSV_PATH, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                for idx, row in enumerate(rows):
                    if idx > 0 and len(row) > 1 and row[1] == invoice:
                        rows[idx] = [date_str, invoice, name, phone, address, product, cod_amount, status, tracking]
                        updated = True
                        break
        except Exception as e:
            print(f"[CSV Read Error] {e}")

    if not updated:
        new_row = [date_str, invoice, name, phone, address, product, cod_amount, status, tracking]
        if not rows:
            rows = [headers, new_row]
        else:
            rows.append(new_row)

    try:
        with open(ORDERS_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Order #{invoice} logged to CSV successfully.")
    except Exception as e:
        print(f"[CSV Write Error] {e}")


def get_order_by_invoice(invoice: str) -> dict:
    """Retrieve order details from CSV by invoice ID."""
    if not os.path.isfile(ORDERS_CSV_PATH):
        return None
    try:
        with open(ORDERS_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            for row in rows[1:]:
                if len(row) > 1 and row[1] == invoice:
                    return {
                        "date": row[0],
                        "invoice": row[1],
                        "name": row[2],
                        "phone": row[3],
                        "address": row[4],
                        "product": row[5],
                        "cod_amount": row[6],
                        "status": row[7],
                        "tracking": row[8]
                    }
    except Exception as e:
        print(f"[CSV Query Error] {e}")
    return None


def update_order_status_in_csv(invoice: str, new_status: str, tracking_id: str = None):
    """Update status and tracking ID of an order in CSV."""
    if not os.path.isfile(ORDERS_CSV_PATH):
        return
    try:
        with open(ORDERS_CSV_PATH, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        
        for idx in range(1, len(rows)):
            if len(rows[idx]) > 1 and rows[idx][1] == invoice:
                rows[idx][7] = new_status
                if tracking_id:
                    rows[idx][8] = tracking_id
                break
                
        with open(ORDERS_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
    except Exception as e:
        print(f"[CSV Update Error] {e}")


# ==========================================
# 4. STEADFAST BOOKING ENGINE
# ==========================================
def format_steadfast_copy_paste(order: dict) -> str:
    """
    Generate an error-proof copy-paste block for the Steadfast Mobile App or Web Portal.
    """
    invoice = order.get("invoice", "SS-1001")
    name = order.get("name", "")
    phone = order.get("phone", "")
    address = order.get("address", "")
    cod = order.get("cod_amount", "890")
    product = order.get("product", "১ কেজি হানি-নাট মেগা জার")

    slip = (
        f"*Steadfast অ্যাপ/ওয়েবে বুকিং স্লিপ (Copy-Ready):*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*নাম:* `{name}`\n"
        f"*ফোন:* `{phone}`\n"
        f"*ঠিকানা:* `{address}`\n"
        f"*ক্যাশ কালেকশন (COD):* `{cod}`\n"
        f"*ইনভয়েস:* `{invoice}`\n"
        f"*নোট:* `{product} (চেক করে মূল্য পরিশোধ করবে)`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*নির্দেশনা:* উপরের যেকোনো তথ্যে চাপ দিলে তা সরাসরি মোবাইলে কপি হয়ে যাবে!"
    )
    return slip


def book_steadfast_api(order: dict) -> dict:
    """
    Direct REST API call to Steadfast Courier (Phase 2 Auto-Dispatch).
    """
    if STANDBY_MODE:
        return {
            "status": 200,
            "success": True,
            "standby": True,
            "message": "সিস্টেম স্ট্যান্ডবাই মোডে আছে। তথ্য কপি করে অ্যাপে বুকিং দিন।"
        }

    if not STEADFAST_API_KEY or not STEADFAST_SECRET_KEY:
        return {
            "status": 400,
            "success": False,
            "message": "Steadfast API Key অথবা Secret Key কনফিগার করা হয়নি।"
        }

    payload = {
        "invoice": order.get("invoice"),
        "recipient_name": order.get("name"),
        "recipient_phone": order.get("phone"),
        "recipient_address": order.get("address"),
        "cod_amount": float(order.get("cod_amount", 890)),
        "note": f"{order.get('product', 'হানি-নাট মেগা জার')}। কাস্টমার চেক করে টাকা দেবেন।"
    }

    headers = {
        "Api-Key": STEADFAST_API_KEY,
        "Secret-Key": STEADFAST_SECRET_KEY,
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(
            STEADFAST_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == 200:
                cid = data.get("consignment", {}).get("consignment_id", "")
                tracking_code = data.get("consignment", {}).get("tracking_code", cid)
                return {
                    "success": True,
                    "cid": cid,
                    "tracking_code": tracking_code,
                    "raw": data
                }
            else:
                return {
                    "success": False,
                    "message": data.get("message", "Unknown Steadfast error")
                }
    except Exception as e:
        return {"success": False, "message": str(e)}


def parse_order_from_telegram_text(text: str, invoice: str) -> dict:
    """Parse incoming Telegram text message into a structured order dict."""
    order = {
        "invoice": invoice,
        "name": "কাস্টমার",
        "phone": "",
        "address": "",
        "product": "১ কেজি মেগা ফ্যামিলি জার হানি-নাট",
        "cod_amount": "970",
        "note": "চেক করে মূল্য পরিশোধ করবেন",
        "status": "Pending Verification",
        "tracking": "Pending"
    }
    for line in text.split("\n"):
        line = line.strip()
        if "কাস্টমার:" in line:
            order["name"] = line.split(":", 1)[-1].strip()
        elif "মোবাইল:" in line:
            order["phone"] = line.split(":", 1)[-1].replace("`", "").strip()
        elif "ঠিকানা:" in line:
            order["address"] = line.split(":", 1)[-1].strip()
        elif "ক্যাশ অন ডেলিভারি বিল:" in line:
            raw = line.split(":", 1)[-1].replace("৳", "").strip()
            order["cod_amount"] = raw.split(" ")[0].strip()
        elif "নোট:" in line:
            order["note"] = line.split(":", 1)[-1].strip()
    return order


# ==========================================
# 5. TELEGRAM BOT INTERACTIVE LISTENER
# ==========================================
def handle_callback_query(callback: dict):
    """Handle inline button clicks from Sakil in Telegram."""
    callback_id = callback.get("id")
    data = callback.get("data", "")
    from_user = callback.get("from", {}).get("id")
    msg = callback.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")

    # Acknowledge callback immediately
    send_telegram_request("answerCallbackQuery", {
        "callback_query_id": callback_id,
        "text": "প্রসেসিং হচ্ছে...",
        "show_alert": False
    })

    # Extract message text for smart parsing
    msg_text = msg.get("text", "")

    if data.startswith("sf_view_"):
        invoice = data.replace("sf_view_", "")
        order = get_order_by_invoice(invoice)
        if not order and msg_text:
            # Smart parse from incoming order message
            order = parse_order_from_telegram_text(msg_text, invoice)
            log_order_to_csv(order)
        elif not order:
            order = {
                "invoice": invoice,
                "name": "কাস্টমার",
                "phone": "017XXXXXXXX",
                "address": "ঢাকা",
                "cod_amount": "970",
                "product": "১ কেজি মেগা ফ্যামিলি জার হানি-নাট"
            }
        slip_text = format_steadfast_copy_paste(order)
        send_telegram_request("sendMessage", {
            "chat_id": chat_id,
            "text": slip_text,
            "parse_mode": "Markdown"
        })

    elif data.startswith("sf_confirm_"):
        invoice = data.replace("sf_confirm_", "")
        order = get_order_by_invoice(invoice)
        if not order and msg_text:
            order = parse_order_from_telegram_text(msg_text, invoice)
            log_order_to_csv(order)
            
        update_order_status_in_csv(invoice, "Verified & Confirmed", "Pending Booking")
        
        # Sync verified order to Google Sheets
        sheet_synced = False
        if order:
            sheet_synced = send_to_google_sheets(order)

        sheet_note = "\nGoogle Sheets হিসাব খাতায় রিয়েল-টাইমে সংরক্ষিত হয়েছে!" if sheet_synced else ""
        
        confirm_text = (
            f"*অর্ডার #{invoice} কনফার্মড! হিসেবে চিহ্নিত করা হয়েছে!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"গ্রাহকের সাথে কথা বলে অর্ডারটি নিশ্চিত করা হয়েছে।\n"
            f"হিসাব ফাইলে স্ট্যাটাস আপডেট সম্পন্ন হয়েছে।{sheet_note}\n"
            f"পার্সেলটি প্রস্তুত করে Steadfast কুরিয়ারে বুকিং সম্পন্ন করুন।"
        )
        send_telegram_request("sendMessage", {
            "chat_id": chat_id,
            "text": confirm_text,
            "parse_mode": "Markdown"
        })


GOOGLE_SHEET_WEBHOOK_URL = os.getenv(
    "GOOGLE_SHEET_WEBHOOK_URL",
    "https://script.google.com/macros/s/AKfycbwKKNsgwlGI9z1bpLL4IY_p1W05OpvPAaMkFobWsL9QG1NdPpg839veRxUjzqf8WfjTeg/exec"
)

def send_to_google_sheets(order: dict) -> bool:
    """Send verified order to Google Sheets via Apps Script Web App."""
    if not GOOGLE_SHEET_WEBHOOK_URL:
        return False
    try:
        req = urllib.request.Request(
            GOOGLE_SHEET_WEBHOOK_URL,
            data=json.dumps(order).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("status") == "success"
    except Exception as e:
        print(f"[Google Sheet Sync Error] {e}")
        return False


def run_telegram_listener():
    """
    Long polling listener to process callback queries in real-time.
    """
    print("=" * 60)
    print("[ONLINE] SS Iqra Pure Food - Telegram Bot Listener Active")
    print(f"Bot: @ssiqrapurefood_bot | Admin Chat ID: {ADMIN_CHAT_ID}")
    print("Listening for button clicks (WhatsApp, Steadfast Slip, Confirm)...")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    last_update_id = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=40) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                
            if result.get("ok"):
                for update in result.get("result", []):
                    last_update_id = update["update_id"]
                    if "callback_query" in update:
                        handle_callback_query(update["callback_query"])
                    elif "message" in update:
                        msg_text = update["message"].get("text", "")
                        from_id = str(update["message"].get("chat", {}).get("id"))
                        if from_id == str(ADMIN_CHAT_ID) and msg_text.lower() in ["/start", "/status", "status"]:
                            send_telegram_request("sendMessage", {
                                "chat_id": ADMIN_CHAT_ID,
                                "text": (
                                    " *আসসালামু আলাইকুম শাকিল ভাই!*\n\n"
                                    "আপনার SS Iqra Pure Food অর্ডার অটোমেশন পাইপলাইন ১০০% চালু আছে!\n"
                                    "মেসেঞ্জারে কোনো কাস্টমার অর্ডার করা মাত্র এখানে নোটিফিকেশন চলে আসবে ইনশাআল্লাহ।"
                                ),
                                "parse_mode": "Markdown"
                            })
        except KeyboardInterrupt:
            print("\nListener stopped by user.")
            break
        except Exception as e:
            # Sleep briefly on network error
            time.sleep(3)


# ==========================================
# 6. MAIN EXECUTION (DEMO / CLI)
# ==========================================
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--listen":
        run_telegram_listener()
    else:
        # Default: Send a sample live order notification
        print("Sending live test order notification to Sakil's Telegram...")
        sample_order = {
            "invoice": f"SS-{int(time.time()) % 100000}",
            "name": "শাকিল আহাম্মেদ (লাইভ টেস্ট)",
            "phone": "01839611048",
            "address": "মিরপুর, ঢাকা (SS Iqra Pure Food হেডকোয়ার্টার)",
            "product": "১ কেজি মেগা ফ্যামিলি জার হানি-নাট (প্রিমিয়াম কোয়ালিটি)",
            "cod_amount": 890,
            "note": "১০০% খাঁটি সুন্দরবনের মধু ও প্রিমিয়াম ড্রাই ফ্রুটস। চেক করে মূল্য পরিশোধ করবেন।",
            "status": "Pending Verification",
            "tracking": "Pending"
        }
        success = send_order_notification(sample_order)
        if success:
            print("\n[SUCCESS] লাইভ নোটিফিকেশন সফলভাবে পাঠানো হয়েছে!")
            print("আপনার মোবাইলে বা পিসিতে Telegram অ্যাপ চেক করুন।")
            print("To start the interactive button listener, run:")
            print("python telegram_order_manager.py --listen")
