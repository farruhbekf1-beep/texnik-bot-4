#!/usr/bin/env python3
"""
JARVIS / TECH MAX Telegram Bot v5.4 (Python 3 Standalone Server & GitHub).
Tashqi pip paketlar talab qilmaydi (urllib, sqlite3, json, threading).

Xususiyatlari:
 - Kirish va 16 ta Xizmat haqida to'liq ma'lumot
 - 2-bosqichli qat'iy ro'yxatdan o'tish (Ism Familiya -> [📱 Telefon raqamni yuborish])
 - Shaxsiy Taklif Havolasi (Referral link) & Har bir taklif uchun +5% Chegirma
 - Buyurtma berishda chegirmadan foydalanish va Admin rad etsa chegirmani avto-qaytarish
 - Mijozlar uchun: [📋 Admin Javobi / Buyurtma Holati], [🎁 Chegirmalarim], [ℹ️ Biz haqimizda], [💬 Admin bilan aloqa]
 - Admin Panel: [👥 Mijozlar Ro'yxati] (1-click gaplashish), [📋 Buyurtmalar], [📅 Uchrashuvlar], [📊 Statistika],
   [📍 Manzilni O'zgartirish] (Location share), [➕ Yangi Buyruq], [📢 Reklama Yuborish (Broadcast)]
 - Admin buyurtmani qabul qilganda [✅ Qabul qilish] mijozga avtomatik Ustxona Xarita Manzili (sendLocation) borishi
 - 10 minutlik Avto-Uchrashuv taymeri
"""
import json, os, sqlite3, time, urllib.parse, urllib.request, secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime
import threading

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
ADMIN_CHAT_ID = os.environ.get('TECHMAX_ADMIN_CHAT_ID', '').strip()
ADMIN_USERNAME = os.environ.get('TECHMAX_ADMIN_USERNAME', 'FARRUHBEKK1').strip()
ADMIN_PHONE = os.environ.get('TECHMAX_ADMIN_PHONE', '+998507727488').strip()
ADMIN_PHONE_2 = '+998943528488'
BOT_USERNAME = os.environ.get('TECHMAX_BOT_USERNAME', 'texnikalar_tuzymiz_bot').strip()
DB_PATH = os.environ.get('TECHMAX_DB_PATH', 'techmax_bot.sqlite3')
API = f'https://api.telegram.org/bot{TOKEN}/'

# Standart Ustxona Xarita koordinatalari
DEFAULT_LAT = 41.311082
DEFAULT_LON = 69.240562

SERVICES = {
 '⚡ Elektrik Xizmatlari': ['⚡ Elektr montaj binosi', '🔌 Sim yotqizish', '🛡 Panel & Avtomat', '💡 Yoritish tizimi', '🛠 Elektr jihozlar ta\'miri', '🚨 Avariya xizmat (24/7)'],
 '🏠 Aqlli Uy (Smart Home)': ['💡 Yoritish (LED)', '🏃 Harakat sensori', '📹 Kamera va xavfsizlik', '📶 Wi-Fi va internet', '📱 Masofadan boshqaruv'],
 '📱 Telefon Ta\'mirlash': ['🖥 Ekran almashtirish', '🔋 Batareya almashtirish', '🔌 Zaryadlash porti', '📷 Kamera ta\'miri', '⚙️ Dasturiy ta\'mirlash', '💧 Suvdan chiqqan telefon'],
 '💻 Kompyuter & Noutbuk': ['💻 Noutbuk ta\'miri', '🖥 Kompyuter yig\'ish', '🖥 Monitor ta\'miri', '🌐 Tarmoq uskunalar', '⚙️ Dastur o\'rnatish', '🛠 Texnik xizmat'],
 '💻 Dasturlash & Platformalar': ['🌐 Veb saytlar (Landing/Corp)', '✈️ Telegram botlar', '📱 Mobil ilovalar (Android/iOS)', '💻 Desktop dasturlar', '⚙️ API integratsiya & CRM'],
 '✈️ Telegram Botlar': ['🤖 Auto javob bot', '📦 Buyurtma & Xizmatlar bot', '💳 To\'lov tizimi bot', '👥 Foydalanuvchilar boshqaruvi', '📢 Guruh va Kanal botlar'],
 '📱 Android Ilovalar': ['📱 Mobil ilova ishlab chiqish', '🎨 UI/UX dizayn', '🚀 Play Store ga joylash', '⚙️ API integratsiya', '🛠 Yangilash & Qo\'llab-quvvatlash'],
 '⚡ Elektronika Ta\'miri': ['📱 Telefon va gadjetlar', '💻 Kompyuter jihozlari', '🔌 Maishiy texnika', '🛡 Plata ta\'miri', '📐 Sxema va modul'],
 '🚗 Avtomobil Xizmatlari': ['🔌 Diagnostika', '🛢 Moy almashtirish', '⚙️ Filtrlar almashtirish', '🛑 Tormoz tizimi', '🛠 Xodovoy ta\'miri', '❄️ Konditsioner'],
 '🏠 Uy Jihozlari': ['🧺 Kir yuvish mashinasi', '❄️ Sovutgich', '❄️ Konditsioner', '📺 Televizor', '📻 Mikrotulqinli pech'],
 '🎨 Reklama va Dizayn': ['🎨 Logo dizayn', '🖼 Banner va poster', '📱 SMM dizayn', '🎬 Video montaj', '🌐 Web dizayn', '🏷 Brend yaratish'],
 '🌐 Internet va Aloqa': ['📶 Wi-Fi o\'rnatish', '🔌 Internet ulanish', '⚙️ Router sozlash', '🛡 Tarmoq xavfsizligi', '📹 IP kamera'],
 '🚰 Santexnika': ['🚰 Quvur o\'rnatish', '🚰 Kran almashtirish', '🛁 Sanuzel ta\'miri', '🔥 Issiq-suv tizimi', '💧 Suv oqishini bartaraf etish'],
 '🛡 Xavfsizlik Tizimi': ['📹 Kuzatuv kameralar', '🚨 Signalizatsiya', '🔔 Domofon', '🔑 Access control', '📱 Masofadan boshqaruv'],
 '🛵 Skuter xizmatlari': ['🔋 Batareya & Akkumulyator', '⚡ Kontroller & Motor', '🛠 Tormoz & G\'ildiraklar', '⚙️ Skuter Diagnostika']
}

STATE = {}
TEMP = {}

def db():
    c = sqlite3.connect(DB_PATH)
    c.execute('''CREATE TABLE IF NOT EXISTS users(
        chat_id INTEGER PRIMARY KEY, name TEXT, phone TEXT, username TEXT, registered_at TEXT,
        referrer_id INTEGER DEFAULT 0, discount_pct INTEGER DEFAULT 0, invited_count INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, name TEXT, phone TEXT,
        service TEXT, problem TEXT, discount_used INTEGER DEFAULT 0, status TEXT DEFAULT 'PENDING',
        time INTEGER, date_str TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, val TEXT)''')
    c.commit()
    return c

def get_setting(key, default=""):
    c = db()
    row = c.execute("SELECT val FROM settings WHERE key=?", (key,)).fetchone()
    c.close()
    return row[0] if row else default

def set_setting(key, val):
    c = db()
    c.execute("INSERT OR REPLACE INTO settings(key, val) VALUES(?, ?)", (key, str(val)))
    c.commit()
    c.close()

def api(method, data=None):
    try:
        payload = urllib.parse.urlencode({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in (data or {}).items()}).encode()
        req = urllib.request.Request(API + method, data=payload)
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"API Error ({method}):", e)
        return None

def send(chat, text, markup=None):
    d = {'chat_id': chat, 'text': text[:3500]}
    if markup: d['reply_markup'] = markup
    return api('sendMessage', d)

def send_location(chat, lat, lon):
    return api('sendLocation', {'chat_id': chat, 'latitude': lat, 'longitude': lon})

def answer_callback(cb_id, text=""):
    d = {'callback_query_id': cb_id}
    if text: d['text'] = text
    return api('answerCallbackQuery', d)

# ---------- Keyboard Builders ----------
def build_main_menu():
    rows = [
        [{'text': '⚡ Elektrik Xizmatlari'}, {'text': '🏠 Aqlli Uy (Smart Home)'}],
        [{'text': '📱 Telefon Ta\'mirlash'}, {'text': '💻 Kompyuter & Noutbuk'}],
        [{'text': '💻 Dasturlash & Platformalar'}, {'text': '✈️ Telegram Botlar'}],
        [{'text': '📱 Android Ilovalar'}, {'text': '⚡ Elektronika Ta\'miri'}],
        [{'text': '🚗 Avtomobil Xizmatlari'}, {'text': '🏠 Uy Jihozlari'}],
        [{'text': '🎨 Reklama va Dizayn'}, {'text': '🌐 Internet va Aloqa'}],
        [{'text': '🚰 Santexnika'}, {'text': '🛡 Xavfsizlik Tizimi'}],
        [{'text': '🛵 Skuter xizmatlari'}, {'text': '🎁 Chegirmalarim & Taklif Havolasi'}],
        [{'text': '📋 Admin Javobi / Buyurtma Holati'}, {'text': '💬 Qo\'llab-quvvatlash / Admin'}],
        [{'text': 'ℹ️ Biz haqimizda'}]
    ]
    return {'keyboard': rows, 'resize_keyboard': True}

def build_admin_keyboard():
    rows = [
        [{'text': '👥 Mijozlar Ro\'yxati'}, {'text': '📋 Buyurtmalar Ro\'yxati'}],
        [{'text': '📅 Uchrashuvlar (Avto)'}, {'text': '📊 Statistika'}],
        [{'text': '📍 Manzilni O\'zgartirish'}, {'text': '➕ Yangi Buyruq Qo\'shish'}],
        [{'text': '📢 Reklama Yuborish (Broadcast)'}, {'text': '⚙️ Tizim Holati (/status)'}],
        [{'text': '❓ Admin Yordam (/help)'}, {'text': '🔒 Qulflash (/lock)'}]
    ]
    return {'keyboard': rows, 'resize_keyboard': True}

def build_sub_menu(options):
    rows = []
    for i in range(0, len(options), 2):
        r = [{'text': options[i]}]
        if i + 1 < len(options): r.append({'text': options[i + 1]})
        rows.append(r)
    rows.append([{'text': '⬅️ Asosiy Menyuga Qaytish'}])
    return {'keyboard': rows, 'resize_keyboard': True}

def build_contact_keyboard():
    return {'keyboard': [[{'text': '📱 Telefon raqamni yuborish', 'request_contact': True}]], 'resize_keyboard': True, 'one_time_keyboard': True}

def build_location_keyboard():
    return {'keyboard': [[{'text': '📍 Ustxona manzilini yuborish', 'request_location': True}]], 'resize_keyboard': True, 'one_time_keyboard': True}

def build_start_intro_inline():
    return {'inline_keyboard': [[{'text': '✅ Tanishib chiqdim / Ro\'yxatdan o\'tish', 'callback_data': 'start_reg'}]]}

def build_admin_order_inline(order_id, customer_chat_id):
    return {'inline_keyboard': [
        [{'text': '✅ Qabul qilish', 'callback_data': f'acc_{order_id}'}, {'text': '❌ Rad etish', 'callback_data': f'rej_{order_id}'}],
        [{'text': '💬 Mijozga yozish', 'callback_data': f'msg_{customer_chat_id}'}]
    ]}

def build_customer_message_inline(customer_chat_id, name):
    return {'inline_keyboard': [[{'text': f'💬 {name} bilan gaplashish', 'callback_data': f'msg_{customer_chat_id}'}]]}

# ---------- 10 Minutlik Avto-Uchrashuv Taymeri ----------
def check_auto_appointments():
    c = db()
    now = int(time.time())
    orders = c.execute("SELECT id, chat_id, name, phone, service, problem, time FROM orders WHERE status='PENDING'").fetchall()
    owner = ADMIN_CHAT_ID
    for oid, chat_id, name, phone, service, problem, t_time in orders:
        if now - t_time > 600: # 10 minut
            c.execute("UPDATE orders SET status='AUTO_SCHEDULED' WHERE id=?", (oid,))
            c.commit()
            cust_msg = f"⏰ DIQQAT! Buyurtmangiz (# {oid}) bo'yicha Admin 10 minut ichida javob berolmagani sababli uchrashuv avtomatik ravishda tasdiqlandi!\n\n📅 UCHRASHUV TAYINLANDI!\n🛠 Xizmat: {service}\n📝 Muammo: {problem}\n\n📞 Admin tez orada siz bilan bog'lanadi."
            send(chat_id, cust_msg, build_main_menu())
            if owner:
                admin_msg = f"⏰ DIQQAT! BUYURTMA #{oid} UCHRASHUVLAR RO'YXATIGA YOZILDI (10 MINUT UTDI)!\n\n👤 Mijoz: {name}\n📞 Tel: {phone}\n🛠 Xizmat: {service}\n📝 Muammo: {problem}\n\n📌 Iltimos, mijoz bilan bog'laning!"
                send(int(owner), admin_msg, build_admin_keyboard())
    c.close()

def auto_timer_loop():
    while True:
        try:
            check_auto_appointments()
        except Exception as e:
            print("Auto timer error:", e)
        time.sleep(30)

# ---------- Order Creation with Discount ----------
def create_and_send_order(chat, user, service_name, problem, discount_used, username):
    c = db()
    now_ts = int(time.time())
    date_str = datetime.now().strftime('%H:%M %d.%m.%Y')
    c.execute("INSERT INTO orders (chat_id, name, phone, service, problem, discount_used, status, time, date_str) VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)",
              (chat, user[1], user[2], service_name, problem, discount_used, now_ts, date_str))
    c.commit()
    oid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()

    disc_text = f"\n🎁 Qo'llanilgan Chegirma: {discount_used}%" if discount_used > 0 else ""
    send(chat, f"✅ Buyurtmangiz qabul qilindi! (#{oid}){disc_text}\n\n🛠 Xizmat: {service_name}\n📝 Muammo: {problem}\n\n⏰ Admin 10 minut ichida javob bermasa, uchrashuv avtomatik tasdiqlanadi!", build_main_menu())

    if ADMIN_CHAT_ID:
        admin_alert = f"🔔 YANGI BUYURTMA #{oid}!\n\n👤 Mijoz: {user[1]}\n📞 Tel: {user[2]}\n💬 Username: @{username if username else 'yoq'}\n🛠 Xizmat: {service_name}\n📝 Muammo: {problem}{disc_text}\n\n⏱ 10 minut ichida javob berilmasa, avto-uchrashuv tayinlanadi!"
        send(int(ADMIN_CHAT_ID), admin_alert, build_admin_order_inline(oid, chat))

# ---------- Message Handling ----------
def handle_message(m):
    global ADMIN_CHAT_ID
    chat = m['chat']['id']
    from_obj = m.get('from', {})
    username = from_obj.get('username', '').strip()
    text = m.get('text', '').strip()
    lower = text.lower()
    contact = m.get('contact')
    location = m.get('location')

    # Admin verification / pairing mode
    if not ADMIN_CHAT_ID:
        if username.lower() == ADMIN_USERNAME.lower() or text == "123456":
            ADMIN_CHAT_ID = str(chat)
            set_setting("admin_chat_id", ADMIN_CHAT_ID)
            STATE[chat] = "AWAITING_ADMIN_LOC"
            send(chat, "🎉 Admin muvaffaqiyatli ulandi!\n\nIltimos, Ustxonangiz / Servis markazingiz manzilini (Location) yuboring (Pastdagi [📍 Ustxona manzilini yuborish] tugmasini bosing):", build_location_keyboard())
            return

    # ADMIN COMMANDS (Owner Chat)
    if str(chat) == str(ADMIN_CHAT_ID):
        st = STATE.get(chat, "")

        # Admin Broadcast Mode
        if st == "AWAITING_BROADCAST_MSG":
            if lower in ["/cancel", "bekor qilish"]:
                STATE[chat] = ""
                send(chat, "❌ Reklama yuborish bekor qilindi.", build_admin_keyboard())
                return
            STATE[chat] = ""
            c = db()
            users = c.execute("SELECT chat_id FROM users").fetchall()
            c.close()
            count = 0
            for (u_chat,) in users:
                if u_chat:
                    send(u_chat, f"📢 XABAR / REKLAMA:\n\n{text}", build_main_menu())
                    count += 1
            send(chat, f"🚀 Reklama {count} ta ro'yxatdan o'tgan mijozlarga muvaffaqiyatli yetkazildi!", build_admin_keyboard())
            return

        # Admin Location Receiving
        if st == "AWAITING_ADMIN_LOC" or location:
            if location:
                lat = location.get('latitude', DEFAULT_LAT)
                lon = location.get('longitude', DEFAULT_LON)
                set_setting("loc_lat", lat)
                set_setting("loc_lon", lon)
                STATE[chat] = ""
                send(chat, f"✅ Ustxona manzili muvaffaqiyatli saqlandi: {lat}, {lon}\n\nEndi mijozlar buyurtmalari qabul qilinganda ushbu manzil avtomatik yuboriladi.", build_admin_keyboard())
                send_location(chat, lat, lon)
                return

        # Admin Messaging to Customer
        if st.startswith("AWAITING_ADMIN_MSG_"):
            if lower in ["/cancel", "bekor qilish"]:
                STATE[chat] = ""
                send(chat, "❌ Xabar yuborish bekor qilindi.", build_admin_keyboard())
                return
            cust_chat = st.replace("AWAITING_ADMIN_MSG_", "").strip()
            STATE[chat] = ""
            send(int(cust_chat), f"💬 ADMIN JAVOBI:\n\n{text}", build_main_menu())
            send(chat, "✅ Xabaringiz mijozga yetkazildi.", build_admin_keyboard())
            return

        if lower in ["📢 reklama yuborish (broadcast)", "/broadcast", "reklama"]:
            STATE[chat] = "AWAITING_BROADCAST_MSG"
            send(chat, "📢 BARCHA MIJOZLARGA REKLAMA YUBORISH:\n\nBarcha ro'yxatdan o'tgan mijozlarga yuboriladigan reklama/xabarnoma matnini kiriting (bekor qilish uchun /cancel):")
            return

        if lower in ["📍 manzilni o'zgartirish", "/setloc"]:
            STATE[chat] = "AWAITING_ADMIN_LOC"
            send(chat, "📍 Ustxonangiz / Servis markazingiz yangi manzilini yuboring (Pastdagi [📍 Ustxona manzilini yuborish] tugmasini bosing yoki Telegram xaritasidan koordinatali manzil yuboring):", build_location_keyboard())
            return

        if lower in ["👥 mijozlar ro'yxati", "/mijozlar", "mijozlar"]:
            c = db()
            users = c.execute("SELECT chat_id, name, phone, username, registered_at FROM users").fetchall()
            c.close()
            if not users:
                send(chat, "👥 Hozircha ro'yxatdan o'tgan mijozlar yo'q.", build_admin_keyboard())
            else:
                send(chat, f"👥 RO'YXATDAN O'TGAN MIJOZLAR ({len(users)} ta):\nGaplashish uchun mijoz ostidagi [💬 Gaplashish] tugmasini bosing:")
                for idx, (u_chat, name, phone, u_name, reg_at) in enumerate(users, 1):
                    msg = f"{idx}. 👤 {name}\n📞 Tel: {phone}\n💬 ChatID: {u_chat}\n👤 User: @{u_name if u_name else 'yoq'}\n📅 Sana: {reg_at}"
                    send(chat, msg, build_customer_message_inline(u_chat, name))
            return

        if lower in ["📋 buyurtmalar ro'yxati", "📋 buyurtmalar", "/buyurtmalar"]:
            c = db()
            orders = c.execute("SELECT id, name, phone, service, problem, status, date_str, discount_used FROM orders ORDER BY id DESC").fetchall()
            c.close()
            if not orders:
                send(chat, "📋 Hozircha kelib tushgan buyurtmalar yo'q.", build_admin_keyboard())
            else:
                sb = [f"📋 BARCHA BUYURTMALAR ({len(orders)} ta):\n"]
                for oid, name, phone, service, problem, stt, date_str, disc_used in orders:
                    disc_str = f" (🎁 {disc_used}% chegirma)" if disc_used > 0 else ""
                    st_tag = "⏳ Kutilmoqda" if stt == "PENDING" else ("✅ Qabul qilingan" if stt == "ACCEPTED" else ("⏰ Avto-Uchrashuv" if stt == "AUTO_SCHEDULED" else "❌ Rad etilgan"))
                    sb.append(f"🔹 #{oid} [{st_tag}]{disc_str}\n   👤 Mijoz: {name} ({phone})\n   🛠 Xizmat: {service}\n   📝 Muammo: {problem}\n   🕒 {date_str}\n")
                send(chat, "\n".join(sb), build_admin_keyboard())
            return

        if lower in ["📅 uchrashuvlar (avto)", "/uchrashuvlar", "uchrashuvlar"]:
            c = db()
            orders = c.execute("SELECT id, name, phone, service, problem, status, date_str FROM orders WHERE status IN ('AUTO_SCHEDULED', 'ACCEPTED')").fetchall()
            c.close()
            if not orders:
                send(chat, "📅 Hozircha tasdiqlangan yoki avto-tayinlangan uchrashuvlar yo'q.", build_admin_keyboard())
            else:
                sb = [f"📅 UCHRASHUVLAR RO'YXATI ({len(orders)} ta):\n"]
                for idx, (oid, name, phone, service, problem, stt, date_str) in enumerate(orders, 1):
                    tag = "⏰ 10-Minutlik Avto-Uchrashuv" if stt == "AUTO_SCHEDULED" else "✅ Qabul qilingan"
                    sb.append(f"{idx}. {name} ({tag})\n   📞 Tel: {phone}\n   🛠 Xizmat: {service}\n   📝 Muammo: {problem}\n   🕒 Vaqt: {date_str}\n")
                send(chat, "\n".join(sb), build_admin_keyboard())
            return

        if lower in ["📊 statistika", "/stat", "statistika"]:
            c = db()
            users_cnt = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            orders_cnt = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            pending = c.execute("SELECT COUNT(*) FROM orders WHERE status='PENDING'").fetchone()[0]
            auto_cnt = c.execute("SELECT COUNT(*) FROM orders WHERE status='AUTO_SCHEDULED'").fetchone()[0]
            acc_cnt = c.execute("SELECT COUNT(*) FROM orders WHERE status='ACCEPTED'").fetchone()[0]
            c.close()
            stat_msg = f"📊 JARVIS BOT STATISTIKASI:\n\n👥 Jami Mijozlar: {users_cnt} ta\n📦 Jami Buyurtmalar: {orders_cnt} ta\n⏳ Kutilayotgan: {pending} ta\n⏰ Avto-Uchrashuvlar: {auto_cnt} ta\n✅ Tasdiqlangan: {acc_cnt} ta"
            send(chat, stat_msg, build_admin_keyboard())
            return

        # Admin Adding Custom Command
        if st == "AWAITING_ADDCMD_KEY":
            if lower == "/cancel":
                STATE[chat] = ""
                send(chat, "Bekor qilindi.", build_admin_keyboard())
                return
            TEMP[f"{chat}_cmd_key"] = text.strip().lower()
            STATE[chat] = "AWAITING_ADDCMD_VAL"
            send(chat, f"💬 «{text.strip()}» buyrug'i uchun javob matnini yozing:")
            return

        if st == "AWAITING_ADDCMD_VAL":
            key = TEMP.get(f"{chat}_cmd_key", "")
            if key:
                set_setting(f"custom_cmd_{key}", text.strip())
                STATE[chat] = ""
                send(chat, f"✅ Yangi buyruq saqlandi:\n🔑 {key} ➔ {text.strip()}", build_admin_keyboard())
            return

        if lower in ["➕ yangi buyruq qo'shish", "/addcmd", "yangi buyruq"]:
            if "=" in text:
                parts = text.split("=", 1)
                k = parts[0].replace("/addcmd", "").strip().lower()
                v = parts[1].strip()
                if k and v:
                    set_setting(f"custom_cmd_{k}", v)
                    send(chat, f"✅ Buyruq saqlandi:\n🔑 {k} ➔ {v}", build_admin_keyboard())
                    return
            STATE[chat] = "AWAITING_ADDCMD_KEY"
            send(chat, "➕ Yangi buyruq qo'shish:\n\nAvval buyruq so'zini/nomini yozing (masalan: narxlar):")
            return

        if lower.startswith("/delcmd "):
            k = lower.replace("/delcmd ", "").strip()
            set_setting(f"custom_cmd_{k}", "")
            send(chat, f"🗑 Buyruq o'chirildi: «{k}»", build_admin_keyboard())
            return

        if lower in ["❓ admin yordam (/help)", "/help", "yordam"]:
            help_txt = "🤖 JARVIS ADMIN BOT PANELI\n\n👥 Mijozlar Ro'yxati — mijozlar va 1-click gaplashish\n📋 Buyurtmalar Ro'yxati — kelib tushgan buyurtmalar\n📅 Uchrashuvlar — 10-minutlik avto-uchrashuvlar\n📢 Reklama Yuborish — barcha mijozlarga e'lon\n📍 Manzilni O'zgartirish — ustxona manzilini yuborish\n➕ Yangi Buyruq Qo'shish — maxsus javob buyrug'ini kiritish"
            send(chat, help_txt, build_admin_keyboard())
            return

        # Custom admin dynamic command check
        custom_reply = get_setting(f"custom_cmd_{lower}")
        if custom_reply:
            send(chat, custom_reply, build_admin_keyboard())
            return

    # CUSTOMER FLOW
    c = db()
    user = c.execute("SELECT chat_id, name, phone, username, registered_at, referrer_id, discount_pct, invited_count FROM users WHERE chat_id=?", (chat,)).fetchone()
    c.close()

    st = STATE.get(chat, "")

    # Unregistered User Handling
    if not user:
        if lower.startswith("/start ref_"):
            ref_id = lower.replace("/start ref_", "").strip()
            if ref_id.isdigit() and int(ref_id) != chat:
                TEMP[f"{chat}_ref"] = int(ref_id)

        if st == "AWAITING_NAME":
            clean_text = text.strip()
            if len(clean_text) >= 3 and not clean_text.startswith("/"):
                TEMP[f"{chat}_name"] = clean_text
                STATE[chat] = "AWAITING_PHONE"
                send(chat, f"Rahmat, {clean_text}! 👤\n\n📱 Endi telefon raqamingizni yuboring (pastdagi [📱 Telefon raqamni yuborish] tugmasini bosing yoki yozib yuboring):", build_contact_keyboard())
            else:
                send(chat, "Iltimos, Ism va Familiyangizni harflar bilan to'liq kiriting (masalan: Sobirjanov Farruhbek):")
            return

        if st == "AWAITING_PHONE":
            phone_num = contact.get('phone_number') if contact else text.strip()
            digits = ''.join(ch for ch in phone_num if ch.isdigit() or ch == '+')
            if len(digits) >= 7:
                name = TEMP.get(f"{chat}_name", "Mijoz")
                ref_chat_id = TEMP.get(f"{chat}_ref", 0)
                reg_at = datetime.now().strftime('%Y-%m-%d %H:%M')

                c = db()
                c.execute("INSERT OR REPLACE INTO users (chat_id, name, phone, username, registered_at, referrer_id, discount_pct, invited_count) VALUES (?, ?, ?, ?, ?, ?, 0, 0)",
                          (chat, name, digits, username, reg_at, ref_chat_id))
                c.commit()

                if ref_chat_id != 0:
                    referrer = c.execute("SELECT chat_id, discount_pct, invited_count FROM users WHERE chat_id=?", (ref_chat_id,)).fetchone()
                    if referrer:
                        new_disc = referrer[1] + 5
                        new_inv = referrer[2] + 1
                        c.execute("UPDATE users SET discount_pct=?, invited_count=? WHERE chat_id=?", (new_disc, new_inv, ref_chat_id))
                        c.commit()
                        send(ref_chat_id, f"🎉 AJOYIB YANGILIK!\n\nDo'stingiz ({name}) sizning taklif havolangiz orqali botdan ro'yxatdan o'tdi!\n\n🎁 Sizga +5% chegirma berildi!\n📊 Jami Chegirmangiz: {new_disc}%\n👥 Taklif qilgan do'stlaringiz: {new_inv} ta", build_main_menu())
                c.close()

                STATE[chat] = ""
                send(chat, f"🎉 TABRIKLAYMIZ, {name}! Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\nBotning barcha xizmatlari siz uchun ochildi. Qaysi xizmat bo'yicha yordam kerak bo'lsa pastdagi menyudan tanlang:", build_main_menu())
            else:
                send(chat, "Iltimos, telefon raqamingizni pastdagi [📱 Telefon raqamni yuborish] tugmasini bosib yuboring:", build_contact_keyboard())
            return

        # Intro overview for unregistered users
        intro_msg = """✨ ASSALOMU ALAYKUM! JARVIS XIZMATLAR MARKAZIGA XUSH KELIBSIZ! 🤖✨

🛠 Bizning Markazda Sizga Quyidagi Barcha Professional Xizmatlar Taqdim Etiladi:

⚡ 1. ELEKTRIK XIZMATLARI — Bino va uylarda elektr montaj, avtomat va yoritish
🏠 2. AQLLI UY (SMART HOME) — Harakat sensorlari, LED yoritish va masofadan boshqaruv
📱 3. TELEFON TA'MIRLASH — Ekran, batareya, plata ta'miri va suvdan chiqqan telefonlar
💻 4. KOMPYUTER VA NOUTBUKLAR — Noutbuk ta'miri, dastur o'rnatish va tozalash
💻 5. DASTURLASH VA PLATFORMALAR — Saytlar, Web/Desktop dasturlar va CRM
✈️ 6. TELEGRAM BOTLAR — Auto-javob, to'lov va buyurtma botlari
📱 7. ANDROID ILOVALAR — Mobil ilova yaratish va Play Store'ga joylash
⚡ 8. ELEKTRONIKA TA'MIRI — Har qanday maishiy va elektron plata ta'miri
🚗 9. AVTOMOBIL XIZMATLARI — Diagnostika, moy, tormoz va auto-elektrik
🏠 10. UY JIHOZLARI — Kir yuvish mashinasi, sovutgich, konditsioner ta'miri
🎨 11. REKLAMA VA DIZAYN — Logo, banner, SMM, 3D vizualizatsiya va brending
🌐 12. INTERNET VA ALOQA — Wi-Fi o'rnatish, router sozlash va IP kamera
🚰 13. SANTEXNIKA — Quvur, kran, sanuzel va issiq-suv tizimi
🛡 14. XAVFSIZLIK TIZIMI — Kuzatuv kameralari, signalizatsiya va domofon
🛵 15. SKUTER XIZMATLARI — Akkumulyator, kontroller, motor va diagnostika
💬 16. 24/7 QO'LLAB-QUVVATLASH — Bevosita Admin bilan muloqot

🌟 Barcha xizmatlarimiz yuqori sifat, kafolat va hamyonbop narxlarda ko'rsatiladi!

👇 Barcha xizmatlar bilan tanishgan bo'lsangiz, ro'yxatdan o'tish uchun pastdagi tugmani bosing:"""
        send(chat, intro_msg, build_start_intro_inline())
        return

    # Registered User Commands
    if lower in ["🎁 chegirmalarim & taklif havolasi", "chegirmalarim", "taklif havolasi"]:
        disc_pct = user[6]
        invited = user[7]
        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{chat}"
        enc_link = urllib.parse.quote(ref_link)
        enc_txt = urllib.parse.quote("Jarvis Xizmatlar Markazidan 5% chegirma oling!")
        share_url = f"https://t.me/share/url?url={enc_link}&text={enc_txt}"
        inline_kb = {'inline_keyboard': [[{'text': '🔗 Do\'stlarga Yuborish (Share)', 'url': share_url}]]}

        disc_msg = f"🎁 SIZNING CHEGIRMALARINGIZ VA TAKLIF HAVOLANGIZ\n\n📊 Mavjud Chegirmangiz: {disc_pct}%\n👥 Taklif qilingan do'stlar: {invited} ta\n\n🔗 Sizning Shaxsiy Taklif Havolangiz:\n{ref_link}\n\n💡 Ushbu havolani do'stlaringizga yuboring! Bitta do'stingiz ro'yxatdan o'tsa, sizga +5% chegirma beriladi."
        send(chat, disc_msg, inline_kb)
        return

    if lower in ["💬 qo'llab-quvvatlash / admin", "qo'llab-quvvatlash", "admin"]:
        admin_link = f"https://t.me/{ADMIN_USERNAME}"
        inline_kb = {'inline_keyboard': [[{'text': f'💬 Admin Bilan Bog\'lanish (@{ADMIN_USERNAME})', 'url': admin_link}]]}
        send(chat, f"💬 QO'LLAB-QUVVATLASH XIZMATI\n\nSavollaringiz bo'lsa, bevosita Admin bilan bog'laning:\n\n👤 Telegram Admin: @{ADMIN_USERNAME}\n📱 Telefon: {ADMIN_PHONE} / {ADMIN_PHONE_2}", inline_kb)
        return

    if lower in ["📋 admin javobi / buyurtma holati", "buyurtma holati", "admin javobi"]:
        c = db()
        my_orders = c.execute("SELECT id, service, problem, status, date_str, discount_used FROM orders WHERE chat_id=? ORDER BY id DESC", (chat,)).fetchall()
        c.close()
        if not my_orders:
            send(chat, "📋 Hozircha sizda faol buyurtmalar yo'q. Qaysi xizmat bo'yicha yordam kerak bo'lsa menyudan tanlang!", build_main_menu())
        else:
            sb = [f"📋 SIZNING BUYURTMALARINGIZ ({len(my_orders)} ta):\n"]
            has_accepted = False
            for oid, service, problem, stt, date_str, disc_used in my_orders:
                st_tag = "⏳ Kutilmoqda (Admin ko'rib chiqmoqda)" if stt == "PENDING" else ("✅ Admin qabul qildi! (Ustxona xaritasi yuborildi)" if stt == "ACCEPTED" else ("⏰ Avto-Uchrashuv tasdiqlangan" if stt == "AUTO_SCHEDULED" else "❌ Bekor qilingan"))
                if stt == "ACCEPTED": has_accepted = True
                disc_str = f" (🎁 {disc_used}% chegirma)" if disc_used > 0 else ""
                sb.append(f"🔹 Buyurtma #{oid}{disc_str}\n   🛠 Xizmat: {service}\n   📝 Muammo: {problem}\n   📌 Holat: {st_tag}\n   🕒 Vaqti: {date_str}\n")
            send(chat, "\n".join(sb), build_main_menu())
            if has_accepted:
                lat = float(get_setting("loc_lat", DEFAULT_LAT))
                lon = float(get_setting("loc_lon", DEFAULT_LON))
                send_location(chat, lat, lon)
        return

    if lower in ["⬅️ asosiy menyuga qaytish", "/start", "orqaga"]:
        STATE[chat] = ""
        send(chat, "🏠 Asosiy menyuga qaytildi. Qaysi xizmat bo'yicha yordam kerak?", build_main_menu())
        return

    if st.startswith("AWAITING_PROBLEM:"):
        service_name = st.replace("AWAITING_PROBLEM:", "")
        user_disc = user[6]

        if user_disc > 0:
            TEMP[f"{chat}_svc"] = service_name
            TEMP[f"{chat}_prob"] = text
            STATE[chat] = "AWAITING_DISCOUNT_DECISION"
            inline_kb = {'inline_keyboard': [[
                {'text': f'🎁 Ha, {user_disc}% Chegirmadan Foydalanish', 'callback_data': 'disc_yes'},
                {'text': 'Oddiy Davom Etish (Chegirmasiz)', 'callback_data': 'disc_no'}
            ]]}
            send(chat, f"🎁 Sizning hisobingizda {user_disc}% Chegirma bor!\n\nUshbu buyurtmada {user_disc}% chegirmadan foydalanasizmi?", inline_kb)
            return

        create_and_send_order(chat, user, service_name, text, 0, username)
        STATE[chat] = ""
        return

    # Sub-menu Triggers
    for cat_name, sub_opts in SERVICES.items():
        if cat_name.lower() in lower or any(word in lower for word in cat_name.lower().split()):
            send(chat, f"{cat_name} BO'LIMI:\nQuyidagi yo'nalishlardan birini tanlang:", build_sub_menu(sub_opts))
            return

    # Sub-menu Choice -> Problem Prompt
    for cat_name, sub_opts in SERVICES.items():
        for opt in sub_opts:
            if opt.lower() in lower:
                STATE[chat] = f"AWAITING_PROBLEM:{opt}"
                send(chat, f"🛠 Tanlangan xizmat: {opt}\n\nIltimos, muammoni yoki kerakli ishni batafsil yozib yuboring:")
                return

    if lower in ["biz haqimizda", "ma'lumot", "ℹ️ biz haqimizda"]:
        about_msg = f"ℹ️ JARVIS XIZMATLAR MARKAZI\n\nSifatli ta'mirlash, uylarga borib xizmat ko'rsatish, elektro-maishiy va aqlli tizimlar o'rnatish markazi.\n\n📞 Ishonch Telefonlarimiz:\n• 📱 {ADMIN_PHONE}\n• 📱 {ADMIN_PHONE_2}\n\n📌 Ish vaqti: 24/7 Har kuni\n📍 Ustxona manzili Admin tomonidan buyurtmangiz qabul qilingach avtomatik xaritada yuboriladi."
        send(chat, about_msg, build_main_menu())
        return

    # Direct message to Admin
    admin_alert = f"💬 MIJOZDAN XABAR!\n\n👤 Mijoz: {user[1]}\n📞 Tel: {user[2]}\n💬 ChatID: {chat}\n💬 Username: @{username if username else 'yoq'}\n\n📝 Xabar: {text}"
    if ADMIN_CHAT_ID:
        send(int(ADMIN_CHAT_ID), admin_alert, build_admin_order_inline("0", chat))
    send(chat, "✅ Xabaringiz Adminga yetkazildi. Qaysi xizmat bo'yicha yordam kerak bo'lsa pastdagi menyudan tanlang:", build_main_menu())

# ---------- Callback Query Handling ----------
def handle_callback(cb):
    global ADMIN_CHAT_ID
    cb_id = cb['id']
    data = cb.get('data', '')
    from_obj = cb.get('from', {})
    from_chat = from_obj.get('id', 0)

    if data == 'start_reg':
        answer_callback(cb_id, "Ro'yxatdan o'tish boshlandi")
        STATE[from_chat] = "AWAITING_NAME"
        send(from_chat, "👤 Iltimos, Ism va Familiyangizni to'liq kiriting (masalan: Sobirjanov Farruhbek):")
        return

    if data in ['disc_yes', 'disc_no']:
        c = db()
        user = c.execute("SELECT chat_id, name, phone, username, registered_at, referrer_id, discount_pct FROM users WHERE chat_id=?", (from_chat,)).fetchone()
        svc = TEMP.get(f"{from_chat}_svc", "Xizmat")
        prob = TEMP.get(f"{from_chat}_prob", "")
        current_disc = user[6] if user else 0
        apply_disc = current_disc if data == 'disc_yes' else 0

        answer_callback(cb_id, f"{apply_disc}% chegirma qo'llanildi!" if apply_disc > 0 else "Chegirmasiz davom etilmoqda")

        if apply_disc > 0 and user:
            c.execute("UPDATE users SET discount_pct=0 WHERE chat_id=?", (from_chat,))
            c.commit()

        c.close()
        STATE[from_chat] = ""
        create_and_send_order(from_chat, user, svc, prob, apply_disc, user[3] if user else "")
        return

    if str(from_chat) != str(ADMIN_CHAT_ID):
        answer_callback(cb_id, "Faqat Admin uchun!")
        return

    if data.startswith("acc_"):
        oid = data.replace("acc_", "").strip()
        c = db()
        c.execute("UPDATE orders SET status='ACCEPTED' WHERE id=?", (oid,))
        c.commit()
        order = c.execute("SELECT chat_id, service FROM orders WHERE id=?", (oid,)).fetchone()
        c.close()

        answer_callback(cb_id, "Buyurtma qabul qilindi!")
        send(int(ADMIN_CHAT_ID), f"✅ Buyurtma #{oid} Admin tomonidan qabul qilindi va mijozga ustxona manzili yuborildi.", build_admin_keyboard())

        if order and order[0]:
            cust_chat = order[0]
            svc = order[1]
            lat = float(get_setting("loc_lat", DEFAULT_LAT))
            lon = float(get_setting("loc_lon", DEFAULT_LON))
            accept_msg = f"✅ Buyurtmangiz (#{oid}) Admin tomonidan qabul qilindi!\n\n🛠 Xizmat: {svc}\n📍 Bizning Ustxona / Xizmat Ko'rsatish Manzilimiz:\nIltimos, ushbu manzilga kelishingiz va mahsulot/texnikangizni topshirishingiz mumkin, janob."
            send(cust_chat, accept_msg, build_main_menu())
            send_location(cust_chat, lat, lon)

    elif data.startswith("rej_"):
        oid = data.replace("rej_", "").strip()
        c = db()
        c.execute("UPDATE orders SET status='REJECTED' WHERE id=?", (oid,))
        c.commit()
        order = c.execute("SELECT chat_id, discount_used FROM orders WHERE id=?", (oid,)).fetchone()

        answer_callback(cb_id, "Buyurtma rad etildi.")
        send(int(ADMIN_CHAT_ID), f"❌ Buyurtma #{oid} bekor qilindi.", build_admin_keyboard())

        if order and order[0]:
            cust_chat = order[0]
            disc_used = order[1]
            if disc_used > 0:
                c.execute("UPDATE users SET discount_pct = discount_pct + ? WHERE chat_id=?", (disc_used, cust_chat))
                c.commit()
                send(cust_chat, f"❌ Afsuski, buyurtmangiz (#{oid}) bekor qilindi.\n🎁 Ushbu buyurtmada ishlatilgan {disc_used}% chegirmangiz hisobingizga qaytarildi!", build_main_menu())
            else:
                send(cust_chat, f"❌ Afsuski, buyurtmangiz (#{oid}) hozirda bekor qilindi.", build_main_menu())
        c.close()

    elif data.startswith("msg_"):
        cust_chat = data.replace("msg_", "").strip()
        answer_callback(cb_id, "Xabar yozing")
        STATE[int(ADMIN_CHAT_ID)] = f"AWAITING_ADMIN_MSG_{cust_chat}"
        c = db()
        u = c.execute("SELECT name, phone FROM users WHERE chat_id=?", (cust_chat,)).fetchone()
        c.close()
        cust_name = u[0] if u else "Mijoz"
        cust_phone = u[1] if u else ""
        send(int(ADMIN_CHAT_ID), f"💬 {cust_name} (+{cust_phone}) ga yuboriladigan xabaringizni yozing (bekor qilish uchun /cancel):")

def setup_bot():
    try:
        r = api('getMe')
        if r and r.get('ok'):
            global BOT_USERNAME
            BOT_USERNAME = r.get('result', {}).get('username', BOT_USERNAME)
            print(f"✅ Bot muvaffaqiyatli ulindi: @{BOT_USERNAME}")
    except Exception as e:
        print("Bot init error:", e)

def main():
    if not TOKEN:
        raise SystemExit("XATO: TELEGRAM_BOT_TOKEN muhit o'zgaruvchisini kiriting.")

    setup_bot()

    # Avto 10 minutlik taymerni fonda ishga tushirish
    threading.Thread(target=auto_timer_loop, daemon=True).start()

    print("🚀 JARVIS / TECH MAX Server Telegram Boti faol! To'xtatish uchun Ctrl+C")
    offset = 0
    while True:
        try:
            res = api('getUpdates', {'offset': offset, 'timeout': 25, 'allowed_updates': ['message', 'callback_query']})
            if res and res.get('ok'):
                for u in res.get('result', []):
                    offset = u['update_id'] + 1
                    try:
                        if 'message' in u:
                            handle_message(u['message'])
                        elif 'callback_query' in u:
                            handle_callback(u['callback_query'])
                    except Exception as e:
                        print("Update handling error:", e)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("Poll error:", e)
            time.sleep(3)

if __name__ == '__main__':
    main()
