import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import UserNotParticipant, FloodWait, PeerIdInvalid, UserIsBlocked
from flask import Flask
from threading import Thread

# ----------------- FLASK KEEP-ALIVE SERVER -----------------
web_app = Flask('')

@web_app.route('/')
def home():
    return "⚡ TgBanXBot Status: 100% ONLINE & RUNNING LIVE!"

def run_web():
    # Render assigns port dynamically via PORT env variable, defaulting to 8080
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# ----------------- HARDCODED CREDENTIALS -----------------
API_ID = 33772941
API_HASH = "3b6ab6b1940c87915439bb41e4e80ea8"
BOT_TOKEN = "8580109392:AAH_IASAWo3vAiPAfSNbr_l_Yk8UG72V6R0"

ADMIN_ID = 6132146801
OWNER_HANDLE = "@Znonsence"
PREMIUM_PRICE = "$50 / 💎 Lifetime VIP"

CHANNEL_1_ID = "@nobitabanxunban"
CHANNEL_1_LINK = "https://t.me/nobitabanxunban"
CHANNEL_2_LINK = "https://t.me/+O1CtosbUTxU2ODBl"

REFERRAL_THRESHOLD = 10

# In-Memory Database
users_db = {}

app = Client("TgBanXBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ----------------- HELPER FUNCTIONS -----------------
def get_user_data(user_id):
    if user_id not in users_db:
        users_db[user_id] = {"referrals": 0, "referred_by": None, "is_premium": False}
    return users_db[user_id]

def build_progress_bar(count, total=10):
    filled = int((count / total) * 8)
    filled = min(filled, 8)
    bar = "█" * filled + "░" * (8 - filled)
    return f"[{bar}] {count}/{total}"

async def is_subscribed(client, user_id):
    try:
        member = await client.get_chat_member(CHANNEL_1_ID, user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
        return False
    except Exception:
        return True

# ----------------- COMMAND HANDLERS -----------------

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user = message.from_user
    user_id = user.id
    user_data = get_user_data(user_id)

    # Referral system logic
    if len(message.command) > 1:
        ref_id_str = message.command[1]
        if ref_id_str.isdigit():
            referrer_id = int(ref_id_str)
            if referrer_id != user_id and user_data["referred_by"] is None:
                user_data["referred_by"] = referrer_id
                ref_data = get_user_data(referrer_id)
                ref_data["referrals"] += 1
                
                if ref_data["referrals"] >= REFERRAL_THRESHOLD and not ref_data["is_premium"]:
                    ref_data["is_premium"] = True
                    try:
                        await client.send_message(
                            referrer_id,
                            "🏆 **VIP ACCESS UNLOCKED!**\n\n🎉 Aapne 10 Referrals complete kar liye hain! Aapka **Lifetime Premium Access** activate kar diya gaya hai. ⚡"
                        )
                    except Exception:
                        pass

    sub_status = await is_subscribed(client, user_id)
    badge = "👑 VIP PREMIUM" if user_data["is_premium"] else "🆓 FREE TIER"
    prog_bar = build_progress_bar(user_data["referrals"])

    welcome_caption = (
        f"🌌 ━━━━━━ [ ⚡ **BANXVIP ULTRA SYSTEM** ⚡ ] ━━━━━━ 🌌\n\n"
        f"👋 **Greetings, {user.first_name}!**\n"
        f"└─ *Next-Gen Moderation & Protection Engine*\n\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"🔮 **Account Tier:** `{badge}`\n"
        f"🎯 **Referral Progress:** `{prog_bar}`\n\n"
        f"⚡ **VIP PERKS:**\n"
        f" ├ 🚷 Instant Ban (Users / GC / Channels)\n"
        f" ├ 🔓 Lightning Unban Automation\n"
        f" └ 🛡️ Anti-Raid & Ultra Moderation\n\n"
        f"📢 **MANDATORY CHANNELS:**\n"
        f"1️⃣ [Join Channel 1]({CHANNEL_1_LINK})\n"
        f"2️⃣ [Join Channel 2]({CHANNEL_2_LINK})\n\n"
        f"💡 *Unlock VIP using 10 Referrals OR Purchase instantly for $50.*"
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Channel 1", url=CHANNEL_1_LINK),
            InlineKeyboardButton("📢 Channel 2", url=CHANNEL_2_LINK)
        ],
        [InlineKeyboardButton("🔄 Verify Membership", callback_data="check_join")],
        [
            InlineKeyboardButton("🔗 Referral Link", callback_data="get_ref_link"),
            InlineKeyboardButton("💳 Buy VIP ($50)", callback_data="buy_premium")
        ],
        [
            InlineKeyboardButton("📊 Account Stats", callback_data="my_stats"),
            InlineKeyboardButton("👨‍💻 Contact Owner", url=f"https://t.me/{OWNER_HANDLE.replace('@','')}")
        ]
    ])

    if sub_status and user_data["is_premium"]:
        buttons.inline_keyboard.append(
            [InlineKeyboardButton("⚡ VIP CONTROL PANEL ⚡", callback_data="ban_panel")]
        )

    await message.reply_text(welcome_caption, reply_markup=buttons, disable_web_page_preview=True)

# ----------------- CALLBACK QUERY HANDLER -----------------

@app.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    user_data = get_user_data(user_id)
    data = query.data

    if data == "check_join":
        if await is_subscribed(client, user_id):
            await query.answer("✨ Mandatory Channels Verified!", show_alert=True)
            await query.message.delete()
            await start_handler(client, query.message)
        else:
            await query.answer("❌ Dono Channels ko pehle Join Karein!", show_alert=True)

    elif data == "get_ref_link":
        me = await client.get_me()
        ref_link = f"https://t.me/{me.username}?start={user_id}"
        msg = (
            f"🚀 **YOUR VIP REFERRAL SYSTEM**\n\n"
            f"🔗 **Link:** `{ref_link}`\n\n"
            f"📈 **Progress:** `{user_data['referrals']}/{REFERRAL_THRESHOLD} Referrals`\n"
            f"💡 *Is link ko dosto ko bhejein. 10 Invites hote hi Premium Access unlock ho jayega!*"
        )
        await query.message.reply_text(msg, disable_web_page_preview=True)
        await query.answer()

    elif data == "buy_premium":
        buy_text = (
            f"💎 **PURCHASE VIP PREMIUM ACCESS** 💎\n\n"
            f"💰 **Price:** `{PREMIUM_PRICE}`\n\n"
            f"⚡ **Instant Benefits:**\n"
            f" • Unlimited Ban / Unban Limits\n"
            f" • Priority Bot Speed & Zero Cooldown\n"
            f" • Direct Support & Custom Rules\n\n"
            f"📲 **How to Pay:**\n"
            f"Owner se direct contact karke Crypto/UPI dwara $50 pay karein.\n\n"
            f"👤 **Owner:** {OWNER_HANDLE}"
        )
        pay_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Send Message to Owner", url=f"https://t.me/{OWNER_HANDLE.replace('@','')}")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="check_join")]
        ])
        await query.message.edit_text(buy_text, reply_markup=pay_btn)

    elif data == "my_stats":
        prog_bar = build_progress_bar(user_data["referrals"])
        stats_msg = (
            f"📊 **USER DASHBOARD PROFILE**\n\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"👥 **Referrals:** `{user_data['referrals']}`\n"
            f"📊 **Bar:** `{prog_bar}`\n"
            f"👑 **VIP Status:** {'ACTIVE ✅' if user_data['is_premium'] else 'INACTIVE ❌'}\n"
        )
        await query.message.reply_text(stats_msg)
        await query.answer()

    elif data == "ban_panel":
        if not user_data["is_premium"]:
            await query.answer("🔒 VIP Lock! Pehle 10 Referrals complete karein ya $50 pay karein.", show_alert=True)
            return

        panel_text = (
            "🛡️ **VIP MODERATION CONTROL CENTER**\n\n"
            "⚡ **Available Commands:**\n"
            "├ `/ban @username` - Instant Ban User\n"
            "├ `/unban @username` - Instant Unban User\n"
            "└ `/kick @username` - Remove User\n"
        )
        await query.message.reply_text(panel_text)
        await query.answer()

# ----------------- ADMIN COMMANDS -----------------

@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def admin_stats(client: Client, message: Message):
    total = len(users_db)
    premium = sum(1 for u in users_db.values() if u.get("is_premium", False))
    
    msg = (
        f"👑 **ADMIN SYSTEM DASHBOARD** 👑\n\n"
        f"👥 **Total Registered Users:** `{total}`\n"
        f"💎 **VIP Members:** `{premium}`\n"
        f"🆓 **Free Tier Users:** `{total - premium}`\n"
    )
    await message.reply_text(msg)

@app.on_message(filters.command("addpremium") & filters.user(ADMIN_ID))
async def add_premium(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("⚠️ Usage: `/addpremium <user_id>`")
        return
    
    try:
        target_id = int(message.command[1])
        u_data = get_user_data(target_id)
        u_data["is_premium"] = True
        
        await message.reply_text(f"✅ User `{target_id}` is now a **VIP PREMIUM MEMBER**!")
        try:
            await client.send_message(target_id, "👑 **Owner ne aapka VIP Premium Access manually activate kar diya hai!**")
        except Exception:
            pass
    except ValueError:
        await message.reply_text("❌ Invalid User ID!")

@app.on_message(filters.command("removepremium") & filters.user(ADMIN_ID))
async def remove_premium(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("⚠️ Usage: `/removepremium <user_id>`")
        return
    
    try:
        target_id = int(message.command[1])
        u_data = get_user_data(target_id)
        u_data["is_premium"] = False
        await message.reply_text(f"🔴 User `{target_id}` ka VIP status revoked kar diya gaya hai.")
    except ValueError:
        await message.reply_text("❌ Invalid User ID!")

# ----------------- BROADCAST COMMAND -----------------

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast_handler(client: Client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        await message.reply_text("⚠️ **Usage:**\n1. `/broadcast <Text Message>`\n2. Ya kisi photo/post par reply karke `/broadcast` likhein.")
        return

    status_msg = await message.reply_text("⚡ **Broadcast Process Started...**")
    
    success = 0
    failed = 0
    total_users = len(users_db)

    for user_id in list(users_db.keys()):
        try:
            if message.reply_to_message:
                await message.reply_to_message.copy(chat_id=user_id)
            else:
                broadcast_text = message.text.split(None, 1)[1]
                await client.send_message(chat_id=user_id, text=broadcast_text)
            success += 1
            await asyncio.sleep(0.05)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            failed += 1

    report = (
        f"📢 **BROADCAST COMPLETED**\n\n"
        f"👥 **Total Users:** `{total_users}`\n"
        f"✅ **Successful:** `{success}`\n"
        f"❌ **Failed / Blocked:** `{failed}`"
    )
    await status_msg.edit_text(report)

if __name__ == "__main__":
    keep_alive()  # Web server start for Render Web Service
    print("⚡ Bot Pyrogram Fast Engine Online...")
    app.run()
