"""
╔══════════════════════════════════════════════╗
║  HiRise Super Bot v2.0  |  by king_4626      ║
║  تمام قابلیت‌ها در یک بات                   ║
╚══════════════════════════════════════════════╝
"""
import asyncio
import json
import os
import random
import time
import threading
import requests
from typing import Optional
from asyncio import Task

from flask import Flask
from highrise import BaseBot, User
from highrise.models import Item, Position
from highrise.__main__ import BotDefinition, main as run_bot
from emotes_data import emotes

# ══════════════════════════════════════════════
#  توکن‌ها و تنظیمات
# ══════════════════════════════════════════════
try:
    import tiba
    ROOM_ID = tiba.ROOM_ID
    HIGHRISE_API_TOKEN = tiba.HIGHRISE_API_TOKEN
    OWNER_USERNAME = tiba.OWNER_USERNAME
except ImportError:
    ROOM_ID = os.environ.get("ROOM_ID", "")
    HIGHRISE_API_TOKEN = os.environ.get("HIGHRISE_API_TOKEN", "")
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "king_4626")

# لیست ادمین‌ها (در حین اجرا آپدیت می‌شه)
ADMINS: list[str] = [OWNER_USERNAME]

def is_owner(user: User) -> bool:
    return user.username.lower() == OWNER_USERNAME.lower()

def is_admin(user: User) -> bool:
    return user.username.lower() in [a.lower() for a in ADMINS]

# ══════════════════════════════════════════════
#  Flask Keep-Alive
# ══════════════════════════════════════════════
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 HiRise Bot is running!"

@app.route('/ping')
def ping():
    return "pong"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def start_keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# ══════════════════════════════════════════════
#  دیکشنری طبقات (تلپورت عمومی)
# ══════════════════════════════════════════════
FLOOR_ALIASES = {
    "f1": "floor1", "طبقه1": "floor1", "طبقه ۱": "floor1", "floor1": "floor1",
    "f2": "floor2", "طبقه2": "floor2", "طبقه ۲": "floor2", "floor2": "floor2",
    "f3": "floor3", "طبقه3": "floor3", "طبقه ۳": "floor3", "floor3": "floor3",
    "f4": "floor4", "طبقه4": "floor4", "طبقه ۴": "floor4", "floor4": "floor4",
    "f5": "floor5", "طبقه5": "floor5", "طبقه ۵": "floor5", "floor5": "floor5",
}

# ══════════════════════════════════════════════
#  ست‌های لباس پیش‌فرض بات
# ══════════════════════════════════════════════
DEFAULT_OUTFITS = [
    [
        Item(type='clothing', amount=1, id='body-flesh', account_bound=False, active_palette=27),
        Item(type='clothing', amount=1, id='eye-n_basic2018malesquaresleepy', account_bound=False, active_palette=7),
        Item(type='clothing', amount=1, id='shirt-n_starteritems_vneckwhite', account_bound=False, active_palette=-1),
        Item(type='clothing', amount=1, id='pants-n_starteritems_jeansblue', account_bound=False, active_palette=-1),
        Item(type='clothing', amount=1, id='shoes-n_starteritems_sneakerswhite', account_bound=False, active_palette=-1),
    ],
    [
        Item(type='clothing', amount=1, id='body-flesh', account_bound=False, active_palette=1),
        Item(type='clothing', amount=1, id='eye-n_basic2018malealmondsleepy', account_bound=False, active_palette=2),
        Item(type='clothing', amount=1, id='shirt-n_starteritems_vneckwhite', account_bound=False, active_palette=-1),
        Item(type='clothing', amount=1, id='pants-n_starteritems_jeansblue', account_bound=False, active_palette=-1),
        Item(type='clothing', amount=1, id='shoes-n_starteritems_sneakerswhite', account_bound=False, active_palette=-1),
    ],
    [
        Item(type='clothing', amount=1, id='body-flesh', account_bound=False, active_palette=12),
        Item(type='clothing', amount=1, id='hair_front-n_malenew33', account_bound=False, active_palette=-1),
        Item(type='clothing', amount=1, id='hair_back-n_malenew33', account_bound=False, active_palette=-1),
        Item(type='clothing', amount=1, id='pants-n_starteritems2019mensshortsblue', account_bound=False, active_palette=-1),
        Item(type='clothing', amount=1, id='shoes-n_whitedans', account_bound=False, active_palette=-1),
    ],
]

# نقشه گلد بار
GOLD_BARS = {
    1: "gold_bar_1", 5: "gold_bar_5", 10: "gold_bar_10",
    50: "gold_bar_50", 100: "gold_bar_100", 500: "gold_bar_500",
    1000: "gold_bar_1000", 5000: "gold_bar_5000", 10000: "gold_bar_10000"
}

def get_tip_bar(amount: int):
    """بهترین گلد بار برای مقدار مشخص"""
    bars = sorted(GOLD_BARS.keys(), reverse=True)
    for b in bars:
        if amount >= b:
            return GOLD_BARS[b], b
    return "gold_bar_1", 1

# ══════════════════════════════════════════════
#  بات اصلی
# ══════════════════════════════════════════════
class HiRiseBot(BaseBot):

    def __init__(self):
        super().__init__()
        self.db_file = "bot_data.json"

        # ── وضعیت‌های قابل toggle ──
        self.welcome_enabled = True       # خوشامدگویی
        self.goodbye_enabled = True       # خداحافظی
        self.dance_enabled = True         # دنس برای همه
        self.auto_tp_enabled = False      # تلپورت خودکار بات
        self.fly_enabled = False          # حالت پرواز (گاوش)

        # ── پیام‌های قابل تنظیم ──
        self.welcome_text = "🎉 سلام {user} عزیز! به روم ما خوش اومدی 🤍"
        self.goodbye_text  = "👋 {user} خداحافظ، مراقب خودت باش 🤍"

        # ── اسپم ──
        self.spam_active = False
        self.spam_task: Optional[Task] = None
        self.spam_message = ""
        self.spam_interval = 1.0

        # ── دنس کاربران (حلقه دائمی) ──
        self.user_dances: dict[str, Task] = {}  # {user_id: task}

        # ── دنس کل روم ──
        self.room_dance_active = False
        self.room_dance_emote_id: str = ""
        self.room_dance_duration: float = 5.0
        self.room_dance_task: Optional[Task] = None

        # ── دنس بات (حلقه دائمی) ──
        self.bot_dance_task: Optional[Task] = None
        self.bot_dance_emote: str = ""

        # ── فالو ──
        self.follow_target_id: Optional[str] = None
        self.follow_task: Optional[Task] = None

        # ── فریز (زندان) ──
        self.frozen_users: dict[str, Task] = {}  # {user_id: loop_task}

        # ── پرواز کاربران (گاوش) ──
        self.flying_users: dict[str, Task] = {}

        # ── موقعیت‌های ذخیره‌شده ──
        self.locations: dict = {}        # {name: {x,y,z,facing}}
        self.floor_locations: dict = {}  # {floor_key: {x,y,z,facing}}
        self.admin_spots: dict = {}      # {name: {x,y,z,facing}} فقط ادمین

        # ── auto-tp بات ──
        self.auto_tp_position: Optional[dict] = None
        self.auto_tp_task: Optional[Task] = None

        # ── فریز همه ──
        self.freeze_all_active = False
        self.freeze_all_task: Optional[Task] = None

        # ── تاس ──
        self.dice_game: dict = {}  # {user_id: {bet, target}}

        # ── آمار ──
        self.total_visitors = 0
        self.message_counts: dict[str, int] = {}

        # ── ادمین‌ها ──
        self.extra_admins: list[str] = []

        # ── دیکشنری دنس‌ها ──
        self.emotes_list = emotes
        self.emotes_by_index = {i+1: e for i, e in enumerate(emotes)}
        self.emotes_by_name = {e.name.lower(): e for e in emotes}
        self.emotes_by_id   = {e.id.lower(): e for e in emotes}

        # ── بارگذاری داده ──
        self._load_data()

        # ── تیپ گلد ──
        self.tip_history: list[str] = []

    # ══════════════════════════════════════════
    #  ذخیره/بارگذاری
    # ══════════════════════════════════════════
    def _load_data(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.locations       = d.get("locations", {})
                self.floor_locations = d.get("floor_locations", {})
                self.admin_spots     = d.get("admin_spots", {})
                self.welcome_text    = d.get("welcome_text", self.welcome_text)
                self.goodbye_text    = d.get("goodbye_text",  self.goodbye_text)
                self.welcome_enabled = d.get("welcome_enabled", True)
                self.goodbye_enabled = d.get("goodbye_enabled",  True)
                self.extra_admins    = d.get("extra_admins", [])
                for a in self.extra_admins:
                    if a.lower() not in [x.lower() for x in ADMINS]:
                        ADMINS.append(a)
                print("✅ داده‌ها بارگذاری شدند")
            except Exception as e:
                print(f"⚠️ خطا در بارگذاری: {e}")

    def _save_data(self):
        try:
            data = {
                "locations":       self.locations,
                "floor_locations": self.floor_locations,
                "admin_spots":     self.admin_spots,
                "welcome_text":    self.welcome_text,
                "goodbye_text":    self.goodbye_text,
                "welcome_enabled": self.welcome_enabled,
                "goodbye_enabled": self.goodbye_enabled,
                "extra_admins":    self.extra_admins,
            }
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ خطا در ذخیره: {e}")

    # ══════════════════════════════════════════
    #  on_start
    # ══════════════════════════════════════════
    async def on_start(self, session_metadata) -> None:
        print("✅ بات وصل شد!")
        await self.highrise.chat("✅ بات فعاله | تایپ !help برای دستورات")
        asyncio.create_task(self._auto_save_loop())
        asyncio.create_task(self._heartbeat_loop())

    # ══════════════════════════════════════════
    #  حلقه‌های پس‌زمینه
    # ══════════════════════════════════════════
    async def _heartbeat_loop(self):
        while True:
            try:
                await self.highrise.send_emote("idle-loop-happy")
                await asyncio.sleep(28)
            except Exception as e:
                print(f"💓 heartbeat error: {e}")
                await asyncio.sleep(10)

    async def _auto_save_loop(self):
        while True:
            await asyncio.sleep(60)
            self._save_data()

    # ══════════════════════════════════════════
    #  on_user_join
    # ══════════════════════════════════════════
    async def on_user_join(self, user: User, position) -> None:
        self.total_visitors += 1
        if self.welcome_enabled:
            try:
                msg = self.welcome_text.replace("{user}", user.username)
                await self.highrise.chat(msg)
                await self.highrise.send_emote("emote-wave")
            except Exception as e:
                print(f"on_user_join error: {e}")
        # اگه دنس روم فعاله، کاربر جدید هم همون دنس رو بزنه
        if self.room_dance_active and self.room_dance_emote_id:
            try:
                await asyncio.sleep(1.5)   # یه لحظه صبر تا کاربر لود بشه
                await self.highrise.send_emote(self.room_dance_emote_id, user.id)
            except Exception:
                pass

    # ══════════════════════════════════════════
    #  on_user_leave
    # ══════════════════════════════════════════
    async def on_user_leave(self, user: User) -> None:
        # پاک‌سازی دنس
        if user.id in self.user_dances:
            self.user_dances[user.id].cancel()
            del self.user_dances[user.id]
        # پاک‌سازی فریز
        if user.id in self.frozen_users:
            self.frozen_users[user.id].cancel()
            del self.frozen_users[user.id]
        if user.id in self.flying_users:
            self.flying_users[user.id].cancel()
            del self.flying_users[user.id]
        # خداحافظی
        if self.goodbye_enabled:
            try:
                msg = self.goodbye_text.replace("{user}", user.username)
                await self.highrise.chat(msg)
            except Exception as e:
                print(f"on_user_leave error: {e}")

    # ══════════════════════════════════════════
    #  on_tip
    # ══════════════════════════════════════════
    async def on_tip(self, sender: User, receiver: User, tip) -> None:
        try:
            await self.highrise.chat(f"💰 ممنون از سخاوت @{sender.username}! 🙏❤️")
            await self.highrise.send_emote("emote-receive-happy")
        except Exception as e:
            print(f"on_tip error: {e}")

    # ══════════════════════════════════════════
    #  on_chat — پردازش دستورات
    # ══════════════════════════════════════════
    async def on_chat(self, user: User, message: str) -> None:
        try:
            msg = message.strip()
            uid = user.id
            uname = user.username

            self.message_counts[uname] = self.message_counts.get(uname, 0) + 1

            # ═══ هلپ ═══
            if msg.lower() in ["!help", "!راهنما", "help", "راهنما"]:
                await self._send_help(user)
                return

            msg_low = msg.lower()

            # ═══ دنس با لینک هایرایز ═══
            # مثال: https://high.rs/item?id=dance-floss&type=emote
            link_emote_id = self._parse_highrise_link(msg)
            if link_emote_id:
                if not self.dance_enabled and not is_admin(user):
                    await self.highrise.chat("🔴 دنس غیرفعاله!")
                    return
                emote = self.emotes_by_id.get(link_emote_id.lower())
                name_display = emote.name if emote else link_emote_id
                duration = emote.duration if emote else 5.0
                await self.highrise.chat(f"🎵 {uname} داره «{name_display}» میزنه!")
                await self._start_user_and_bot_dance(uid, link_emote_id, duration)
                return

            # ═══ دستورات عددی (دنس) ═══
            if msg.isdigit():
                dance_num = int(msg)
                if 1 <= dance_num <= len(self.emotes_list):
                    if not self.dance_enabled and not is_admin(user):
                        await self.highrise.chat("🔴 دنس غیرفعاله!")
                        return
                    emote = self.emotes_by_index[dance_num]
                    await self.highrise.chat(f"🎵 {uname} داره «{emote.name}» میزنه!")
                    await self._start_user_and_bot_dance(uid, emote.id, emote.duration)
                else:
                    await self.highrise.chat(f"❌ عدد بین 1 تا {len(self.emotes_list)} بزن")
                return

            # ═══ دنس با اسم ═══
            if msg_low in self.emotes_by_name:
                if not self.dance_enabled and not is_admin(user):
                    await self.highrise.chat("🔴 دنس غیرفعاله!")
                    return
                emote = self.emotes_by_name[msg_low]
                await self.highrise.chat(f"🎵 {uname} داره «{emote.name}» میزنه!")
                await self._start_user_and_bot_dance(uid, emote.id, emote.duration)
                return

            # ═══ دنس با ID خام ═══
            if msg_low in self.emotes_by_id:
                if not self.dance_enabled and not is_admin(user):
                    await self.highrise.chat("🔴 دنس غیرفعاله!")
                    return
                emote = self.emotes_by_id[msg_low]
                await self.highrise.chat(f"🎵 {uname} داره «{emote.name}» میزنه!")
                await self._start_user_and_bot_dance(uid, emote.id, emote.duration)
                return

            # ═══ استپ دنس ═══
            if msg_low in ["stop", "توقف", "/stop", "0"]:
                await self._stop_user_dance(uid)
                # بات هم متوقف میشه
                if self.bot_dance_task and not self.bot_dance_task.done():
                    self.bot_dance_task.cancel()
                    self.bot_dance_task = None
                    self.bot_dance_emote = ""
                await self.highrise.chat(f"⛔ دنس {uname} و بات متوقف شد")
                return

            # ═══ تلپورت به طبقه (عمومی) ═══
            if msg_low in FLOOR_ALIASES:
                floor_key = FLOOR_ALIASES[msg_low]
                if floor_key in self.floor_locations:
                    pos = self._dict_to_pos(self.floor_locations[floor_key])
                    await self.highrise.teleport(uid, pos)
                    await self.highrise.chat(f"✨ {uname} به {floor_key} تلپورت شد!")
                else:
                    await self.highrise.chat(f"❌ طبقه {floor_key} هنوز تنظیم نشده!")
                return

            # ─────────────────── ادمین دستورات ───────────────────

            # ═══ اسپم ═══
            if msg_low.startswith("!spam ") and is_admin(user):
                await self._cmd_spam_start(user, msg)
                return
            if msg_low in ["!stopspam", "!spam stop", "!اسپم‌آف"] and is_admin(user):
                await self._cmd_spam_stop()
                return

            # ═══ خوشامد / خداحافظی ═══
            if msg_low in ["!welkon", "!خوشامدآن"] and is_admin(user):
                self.welcome_enabled = True
                self._save_data()
                await self.highrise.chat("✅ خوشامدگویی فعال شد!")
                return
            if msg_low in ["!welkoff", "!خوشامدآف"] and is_admin(user):
                self.welcome_enabled = False
                self._save_data()
                await self.highrise.chat("🔴 خوشامدگویی غیرفعال شد!")
                return
            if msg_low in ["!byeon", "!خداحافظیآن"] and is_admin(user):
                self.goodbye_enabled = True
                self._save_data()
                await self.highrise.chat("✅ خداحافظی فعال شد!")
                return
            if msg_low in ["!byeoff", "!خداحافظیآف"] and is_admin(user):
                self.goodbye_enabled = False
                self._save_data()
                await self.highrise.chat("🔴 خداحافظی غیرفعال شد!")
                return

            # تغییر متن خوشامد
            if msg.startswith("!setwelcome ") and is_admin(user):
                self.welcome_text = msg[12:].strip()
                self._save_data()
                await self.highrise.chat(f"✅ متن خوشامد آپدیت شد!")
                return
            if msg.startswith("!setgoodbye ") and is_admin(user):
                self.goodbye_text = msg[12:].strip()
                self._save_data()
                await self.highrise.chat(f"✅ متن خداحافظی آپدیت شد!")
                return

            # ═══ دنس آن/آف ═══
            if msg_low in ["!danson", "!دنسآن"] and is_admin(user):
                self.dance_enabled = True
                await self.highrise.chat("✅ دنس برای همه فعال شد!")
                return
            if msg_low in ["!dansoff", "!دنسآف"] and is_admin(user):
                self.dance_enabled = False
                await self.highrise.chat("🔴 دنس غیرفعال شد!")
                return

            # ═══ تلپورت به لوکیشن (ادمین) ═══
            if msg.lower().startswith("!tp ") and is_admin(user):
                await self._cmd_tp_to_location(user, msg[4:].strip())
                return
            if msg.lower().startswith("!تلپ ") and is_admin(user):
                await self._cmd_tp_to_location(user, msg[5:].strip())
                return

            # ═══ ذخیره لوکیشن ═══
            if msg.lower().startswith("!save ") and is_admin(user):
                await self._cmd_save_location(user, msg[6:].strip())
                return
            if msg.lower().startswith("!حفظ ") and is_admin(user):
                await self._cmd_save_location(user, msg[5:].strip())
                return

            # ═══ ذخیره طبقه ═══
            if msg.lower().startswith("!setfloor ") and is_admin(user):
                await self._cmd_set_floor(user, msg[10:].strip())
                return

            # ═══ لیست لوکیشن‌ها ═══
            if msg_low in ["!locs", "!locations", "!لوکیشن‌ها"] and is_admin(user):
                locs = list(self.locations.keys())
                floors = list(self.floor_locations.keys())
                txt = "📍 لوکیشن‌ها:\n" + ("\n".join(locs) if locs else "—")
                txt += "\n🏢 طبقات:\n" + ("\n".join(floors) if floors else "—")
                await self.highrise.chat(txt)
                return

            # ═══ حذف لوکیشن ═══
            if msg.lower().startswith("!delloc ") and is_admin(user):
                name = msg[8:].strip().lower()
                if name in self.locations:
                    del self.locations[name]
                    self._save_data()
                    await self.highrise.chat(f"🗑️ لوکیشن '{name}' حذف شد")
                else:
                    await self.highrise.chat(f"❌ لوکیشن '{name}' پیدا نشد")
                return

            # ═══ اسپات ادمین ═══
            if msg.lower().startswith("!setspot ") and is_admin(user):
                await self._cmd_set_spot(user, msg[9:].strip())
                return
            if msg.lower().startswith("!gospot ") and is_admin(user):
                await self._cmd_go_spot(user, msg[8:].strip())
                return
            if msg_low in ["!spots"] and is_admin(user):
                spots = list(self.admin_spots.keys())
                await self.highrise.chat("📍 اسپات‌ها:\n" + ("\n".join(spots) if spots else "—"))
                return

            # ═══ تلپورت خودکار بات (آن/آف) ═══
            if msg_low in ["!autotpon", "!اتوتلپ‌آن"] and is_admin(user):
                await self._cmd_auto_tp_on(user)
                return
            if msg_low in ["!autotpoff", "!اتوتلپ‌آف"] and is_admin(user):
                await self._cmd_auto_tp_off()
                return

            # ═══ بردن کنار خودم ═══
            if msg.lower().startswith("!bring ") and is_admin(user):
                await self._cmd_bring(user, msg[7:].strip())
                return
            if msg.lower().startswith("!بیار ") and is_admin(user):
                await self._cmd_bring(user, msg[6:].strip())
                return

            # ═══ رفتن پیش کاربر ═══
            if msg.lower().startswith("!goto ") and is_admin(user):
                await self._cmd_goto(user, msg[6:].strip())
                return
            if msg.lower().startswith("!برو ") and is_admin(user):
                await self._cmd_goto(user, msg[5:].strip())
                return

            # ═══ تلپورت همه (ادمین) به یه جا ═══
            if msg.lower().startswith("!tpall ") and is_admin(user):
                await self._cmd_tpall(user, msg[7:].strip())
                return

            # ═══ تلپورت بات ═══
            if msg.lower().startswith("!movebot ") and is_admin(user):
                await self._cmd_move_bot(user, msg[9:].strip())
                return

            # ═══ فالو ═══
            if msg.lower().startswith("!follow ") and is_admin(user):
                await self._cmd_follow_start(user, msg[8:].strip())
                return
            if msg_low in ["!unfollow", "!stopfollow", "!فالوآف"] and is_admin(user):
                await self._cmd_follow_stop()
                return

            # ═══ دنس بات ═══
            if msg.lower().startswith("!botdance ") and is_admin(user):
                await self._cmd_bot_dance(user, msg[10:].strip())
                return
            if msg_low in ["!stopdance", "!botdancestop"] and is_admin(user):
                await self._cmd_bot_dance_stop()
                return

            # ═══ رست ═══
            if msg_low in ["!rest", "رست", "!رست"] and is_admin(user):
                await self.highrise.send_emote("sit-idle-cute")
                await self.highrise.chat("😴 بات نشست!")
                return

            # ═══ دنس کل روم ═══
            if msg_low.startswith("!danceall") and is_admin(user):
                arg = msg[9:].strip()
                await self._cmd_danceall(user, arg)
                return
            if msg_low in ["!stopdanceall", "!رقص‌کل‌آف", "!stoproomdance"] and is_admin(user):
                await self._cmd_stopdanceall()
                return

            # ═══ فلوس ═══
            if msg_low in ["!floss", "فلوس", "!فلوس"] and is_admin(user):
                await self._start_bot_dance("dance-floss", 21.33)
                await self.highrise.chat("💃 فلوس!")
                return

            # ═══ فریز (زندان) ═══
            if msg.lower().startswith("!freeze ") and is_admin(user):
                await self._cmd_freeze(user, msg[8:].strip())
                return
            if msg.lower().startswith("!فریز ") and is_admin(user):
                await self._cmd_freeze(user, msg[6:].strip())
                return
            if msg.lower().startswith("!unfreeze ") and is_admin(user):
                await self._cmd_unfreeze(user, msg[10:].strip())
                return

            # ═══ پرواز (گاوش) ═══
            if msg.lower().startswith("!fly ") and is_admin(user):
                await self._cmd_fly(user, msg[5:].strip(), True)
                return
            if msg.lower().startswith("!unfly ") and is_admin(user):
                await self._cmd_fly(user, msg[7:].strip(), False)
                return

            # ═══ تیپ گلد ═══
            if msg.lower().startswith("!tipall") and is_admin(user):
                await self._cmd_tip_all(user, msg)
                return
            if msg.lower().startswith("!tip ") and is_admin(user):
                await self._cmd_tip_user(user, msg[5:].strip())
                return
            if msg.lower().startswith("!تیپ‌همه") and is_admin(user):
                await self._cmd_tip_all(user, msg)
                return

            # ═══ لباس ═══
            if msg_low in ["!copyoutfit", "!کپی‌لباس", "کپی لباس", "copy my outfit"] and is_admin(user):
                await self._cmd_copy_outfit(user)
                return
            # کپی لباس از کاربر دیگه (کالکشن هم میاد)
            if msg.lower().startswith("!wearoutfit ") and is_admin(user):
                await self._cmd_wear_user_outfit(user, msg[12:].strip())
                return
            if msg.lower().startswith("!wearfree ") and is_admin(user):
                await self._cmd_wear_user_outfit(user, msg[10:].strip(), free_only=True)
                return
            if msg.lower().startswith("!outfit ") and is_admin(user):
                await self._cmd_change_outfit(user, msg[8:].strip())
                return
            if msg.lower().startswith("!لباس ") and is_admin(user):
                await self._cmd_change_outfit(user, msg[6:].strip())
                return
            if msg_low in ["!randoutfit", "!لباس‌رندوم"] and is_admin(user):
                outfit = random.choice(DEFAULT_OUTFITS)
                await self.highrise.set_outfit(outfit)
                await self.highrise.chat("👗 لباس رندوم پوشیده شد!")
                return

            # ═══ مدیریت ادمین ═══
            if msg.lower().startswith("!addadmin ") and is_admin(user):
                new_admin = msg[10:].strip().replace("@", "")
                if new_admin.lower() not in [a.lower() for a in ADMINS]:
                    ADMINS.append(new_admin)
                    self.extra_admins.append(new_admin)
                    self._save_data()
                    await self.highrise.chat(f"✅ @{new_admin} ادمین شد!")
                else:
                    await self.highrise.chat(f"⚠️ @{new_admin} قبلاً ادمینه")
                return
            if msg.lower().startswith("!removeadmin ") and is_owner(user):
                target = msg[13:].strip().replace("@", "")
                if target.lower() == OWNER_USERNAME.lower():
                    await self.highrise.chat("❌ نمی‌تونی مالک رو حذف کنی!")
                    return
                ADMINS[:] = [a for a in ADMINS if a.lower() != target.lower()]
                self.extra_admins = [a for a in self.extra_admins if a.lower() != target.lower()]
                self._save_data()
                await self.highrise.chat(f"🗑️ @{target} از ادمین‌ها حذف شد")
                return
            if msg_low in ["!admins", "!ادمین‌ها"] and is_admin(user):
                lst = "\n".join([f"👤 {a}" + (" 👑" if a.lower() == OWNER_USERNAME.lower() else "") for a in ADMINS])
                await self.highrise.chat(f"📋 ادمین‌ها:\n{lst}")
                return

            # ═══ بازی تاس ═══
            if msg_low in ["!dice", "!تاس", "تاس"]:
                await self._cmd_dice(user)
                return
            if msg_low.startswith("!roll"):
                await self._cmd_roll(user, msg)
                return

            # ═══ لیست دنس‌ها ═══
            if msg_low in ["!danslist", "!لیست‌دنس", "!listdance"]:
                await self._cmd_list_dances()
                return

            # ═══ آپدیت لیست ═══
            if msg_low in ["!status", "!وضعیت"] and is_admin(user):
                await self._cmd_status()
                return


        except Exception as e:
            print(f"⚠️ on_chat error: {e}")

    # ══════════════════════════════════════════
    #  ── هلپ ──
    # ══════════════════════════════════════════
    async def _send_help(self, user: User):
        if is_admin(user):
            help_txt = (
                "━━━ 🤖 دستورات ادمین ━━━\n"
                "🎵 دنس:\n"
                "  [عدد 1-{n}] → دنس کاربر + بات\n"
                "  [اسم یا لینک] → دنس کاربر + بات\n"
                "  stop → توقف دنس\n"
                "  !danceall → کل روم رندوم رایگان\n"
                "  !danceall [عدد/اسم/لینک] → کل روم\n"
                "  !stopdanceall → توقف دنس روم\n"
                "  !botdance [عدد/اسم] → دنس بات\n"
                "  !stopdance → متوقف دنس بات\n"
                "  !danson / !dansoff → دنس آن/آف\n"
                "  !floss → فلوس بات\n"
                "  !rest → استراحت بات\n\n"
                "📢 اسپم:\n"
                "  !spam [ثانیه] [متن]\n"
                "  !stopspam\n\n"
                "👋 خوشامد/خداحافظی:\n"
                "  !welkon / !welkoff\n"
                "  !byeon / !byeoff\n"
                "  !setwelcome [متن]\n"
                "  !setgoodbye [متن]\n\n"
                "🌀 تلپورت:\n"
                "  f1/f2... → طبقه\n"
                "  !setfloor [f1] → ثبت طبقه\n"
                "  !save [نام] → ذخیره لوکیشن\n"
                "  !tp [نام] → تلپورت\n"
                "  !tpall [نام] → تلپورت همه\n"
                "  !bring @user → بیار کنارم\n"
                "  !goto @user → برو پیشش\n"
                "  !movebot [نام] → ببر بات\n"
                "  !autotpon/off → اتوتلپ بات\n\n"
                "❄️ فریز/پرواز:\n"
                "  !freeze @user → فریز\n"
                "  !unfreeze @user\n"
                "  !fly @user → پرواز\n"
                "  !unfly @user\n\n"
                "💰 تیپ:\n"
                "  !tipall [مقدار]\n"
                "  !tip @user [مقدار]\n\n"
                "👗 لباس:\n"
                "  !wearoutfit @user → کپی کامل لباس (کالکشن)\n"
                "  !wearfree @user → فقط آیتم‌های رایگان\n"
                "  !copyoutfit → لباس خود ادمین\n"
                "  !outfit [1-3] → لباس پیش‌فرض\n"
                "  !randoutfit → لباس رندوم\n\n"
                "👤 ادمین:\n"
                "  !addadmin @user\n"
                "  !removeadmin @user (مالک)\n"
                "  !admins\n\n"
                "🎲 تاس:\n"
                "  !dice → تاس رندوم\n"
                "  !roll → عدد 1-6\n\n"
                "🔎 سایر:\n"
                "  !follow @user / !unfollow\n"
                "  !status → وضعیت\n"
                "  !danslist → لیست دنس"
            ).replace("{n}", str(len(self.emotes_list)))
            await self.highrise.chat(help_txt)
        else:
            help_txt = (
                "━━━ 🤖 دستورات ━━━\n"
                "🎵 دنس:\n"
                "  [عدد 1-{n}] → دنس شما\n"
                "  [اسم دنس] → مثلاً: floss\n"
                "  stop → توقف دنس\n"
                "🌀 تلپورت:\n"
                "  f1 / f2 / f3... → طبقه\n"
                "🎲 تاس:\n"
                "  !dice / !roll"
            ).replace("{n}", str(len(self.emotes_list)))
            await self.highrise.chat(help_txt)

    # ══════════════════════════════════════════
    #  ── پارس لینک هایرایز ──
    # ══════════════════════════════════════════
    @staticmethod
    def _parse_highrise_link(msg: str) -> Optional[str]:
        """
        از لینک مثل https://high.rs/item?id=dance-floss&type=emote
        آیدی دنس رو استخراج میکنه.
        اگه لینک معتبر نبود None برمیگردونه.
        """
        msg = msg.strip()
        # پشتیبانی از لینک کامل و یا فقط ?id=...
        if "high.rs/item" in msg or "highrise.game/item" in msg:
            # استخراج id از query string
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(msg)
                params = parse_qs(parsed.query)
                emote_type = params.get("type", [""])[0]
                emote_id   = params.get("id",   [""])[0]
                if emote_type == "emote" and emote_id:
                    return emote_id
            except Exception:
                pass
        return None

    # ══════════════════════════════════════════
    #  ── دنس کاربر ──
    # ══════════════════════════════════════════
    async def _start_user_and_bot_dance(self, user_id: str, emote_id: str, duration: float):
        """کاربر و بات هر دو همزمان همون دنس رو میزنن — تا stop بدن نمیسته."""
        # دنس کاربر
        if user_id in self.user_dances:
            self.user_dances[user_id].cancel()
        task = asyncio.create_task(self._dance_loop(user_id, emote_id, duration))
        self.user_dances[user_id] = task
        # دنس بات (همون دنس)
        await self._start_bot_dance(emote_id, duration)

    async def _start_user_dance(self, user_id: str, emote_id: str, duration: float):
        """فقط دنس کاربر — بدون دنس بات (برای استفاده داخلی)."""
        if user_id in self.user_dances:
            self.user_dances[user_id].cancel()
        task = asyncio.create_task(self._dance_loop(user_id, emote_id, duration))
        self.user_dances[user_id] = task

    async def _dance_loop(self, user_id: str, emote_id: str, duration: float):
        """حلقه بی‌نهایت دنس کاربر — فقط با cancel (از stop) متوقف میشه."""
        try:
            while True:
                await self.highrise.send_emote(emote_id, user_id)
                # یه مقدار کوچیکتر از duration برای بی‌درنگی بین تکرارها
                await asyncio.sleep(max(duration - 0.3, 1.0))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"dance_loop error: {e}")

    async def _stop_user_dance(self, user_id: str):
        if user_id in self.user_dances:
            self.user_dances[user_id].cancel()
            del self.user_dances[user_id]

    # ══════════════════════════════════════════
    #  ── دنس کل روم ──
    # ══════════════════════════════════════════
    async def _cmd_danceall(self, user: User, arg: str):
        """مالک/ادمین → کل روم یه دنس رایگان می‌زنن تا stopdanceall"""
        # پیدا کردن emote از عدد، اسم، لینک، یا خالی (رندوم رایگان)
        emote = None

        if not arg:
            # رندوم از دنس‌های رایگان
            free = [e for e in self.emotes_list if e.is_free]
            emote = random.choice(free) if free else self.emotes_list[0]
        elif self._parse_highrise_link(arg):
            emote_id = self._parse_highrise_link(arg)
            emote = self.emotes_by_id.get(emote_id.lower())
            if not emote:
                # emote ناشناخته‌ست ولی آیدیش رو داریم — مستقیم استفاده می‌کنیم
                from emotes_data import Emote as _E
                emote = _E(name=emote_id, id=emote_id, duration=5.0, is_free=True)
        elif arg.isdigit():
            n = int(arg)
            if 1 <= n <= len(self.emotes_list):
                emote = self.emotes_by_index[n]
        elif arg.lower() in self.emotes_by_name:
            emote = self.emotes_by_name[arg.lower()]
        elif arg.lower() in self.emotes_by_id:
            emote = self.emotes_by_id[arg.lower()]

        if not emote:
            await self.highrise.chat(
                f"❌ دنس پیدا نشد!\n"
                f"مثال‌ها:\n"
                f"  !danceall       ← رندوم رایگان\n"
                f"  !danceall 42    ← عدد\n"
                f"  !danceall floss ← اسم\n"
                f"  !danceall [لینک]"
            )
            return

        # فقط emote های رایگان رو میشه برای بقیه فرستاد
        if not emote.is_free:
            await self.highrise.chat(
                f"⚠️ «{emote.name}» رایگان نیست!\n"
                f"فقط دنس‌های رایگان برای همه کار می‌کنن.\n"
                f"از !danceall بدون آرگومان بزن برای رندوم رایگان."
            )
            return

        # اگه قبلاً دنس روم فعاله، خاموشش کن
        if self.room_dance_active:
            await self._cmd_stopdanceall(silent=True)

        self.room_dance_active  = True
        self.room_dance_emote_id   = emote.id
        self.room_dance_duration   = emote.duration

        # شروع حلقه روم-دنس
        self.room_dance_task = asyncio.create_task(self._room_dance_loop())

        await self.highrise.chat(f"🎉 کل روم داره «{emote.name}» میزنه! | !stopdanceall برای توقف")

    async def _room_dance_loop(self):
        """هر duration ثانیه emote رو به همه کاربران روم می‌فرسته."""
        try:
            while self.room_dance_active:
                try:
                    room_users = await self.highrise.get_room_users()
                    tasks = []
                    for u, _ in room_users.content:
                        tasks.append(
                            self.highrise.send_emote(self.room_dance_emote_id, u.id)
                        )
                    # همه همزمان
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                except Exception as e:
                    print(f"room_dance_loop error: {e}")
                await asyncio.sleep(max(self.room_dance_duration - 0.5, 1.5))
        except asyncio.CancelledError:
            pass

    async def _cmd_stopdanceall(self, silent: bool = False):
        self.room_dance_active = False
        if self.room_dance_task and not self.room_dance_task.done():
            self.room_dance_task.cancel()
            self.room_dance_task = None
        self.room_dance_emote_id = ""
        if not silent:
            await self.highrise.chat("⛔ دنس کل روم متوقف شد!")

    # ══════════════════════════════════════════
    #  ── دنس بات ──
    # ══════════════════════════════════════════
    async def _start_bot_dance(self, emote_id: str, duration: float):
        if self.bot_dance_task:
            self.bot_dance_task.cancel()
        self.bot_dance_emote = emote_id
        self.bot_dance_task = asyncio.create_task(self._bot_dance_loop(emote_id, duration))

    async def _bot_dance_loop(self, emote_id: str, duration: float):
        try:
            while True:
                await self.highrise.send_emote(emote_id)
                await asyncio.sleep(max(duration, 1.0))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"bot_dance_loop error: {e}")

    async def _cmd_bot_dance(self, user: User, arg: str):
        emote = None
        if arg.isdigit():
            n = int(arg)
            if 1 <= n <= len(self.emotes_list):
                emote = self.emotes_by_index[n]
        else:
            if arg.lower() in self.emotes_by_name:
                emote = self.emotes_by_name[arg.lower()]
            elif arg.lower() in self.emotes_by_id:
                emote = self.emotes_by_id[arg.lower()]
        if emote:
            await self._start_bot_dance(emote.id, emote.duration)
            await self.highrise.chat(f"🎭 بات داره «{emote.name}» میزنه!")
        else:
            await self.highrise.chat(f"❌ دنس پیدا نشد! عدد 1-{len(self.emotes_list)} یا اسم دنس بزن")

    async def _cmd_bot_dance_stop(self):
        if self.bot_dance_task:
            self.bot_dance_task.cancel()
            self.bot_dance_task = None
        await self.highrise.chat("⛔ دنس بات متوقف شد")

    # ══════════════════════════════════════════
    #  ── اسپم ──
    # ══════════════════════════════════════════
    async def _cmd_spam_start(self, user: User, msg: str):
        parts = msg.split(" ", 2)
        if len(parts) < 3:
            await self.highrise.chat("❌ فرمت: !spam [ثانیه] [متن]\nمثال: !spam 1 سلام همه!")
            return
        try:
            interval = float(parts[1])
            text = parts[2]
            interval = max(0.5, interval)  # حداقل نیم ثانیه
        except ValueError:
            await self.highrise.chat("❌ عدد ثانیه اشتباهه! مثال: !spam 1 سلام")
            return
        if self.spam_active:
            self.spam_active = False
            if self.spam_task:
                self.spam_task.cancel()
        self.spam_message = text
        self.spam_interval = interval
        self.spam_active = True
        self.spam_task = asyncio.create_task(self._spam_loop())
        await self.highrise.chat(f"📢 اسپم شروع شد | هر {interval}ثانیه | متن: {text}")

    async def _spam_loop(self):
        try:
            while self.spam_active:
                await self.highrise.chat(self.spam_message)
                await asyncio.sleep(self.spam_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"spam_loop error: {e}")
        finally:
            self.spam_active = False

    async def _cmd_spam_stop(self):
        if self.spam_active:
            self.spam_active = False
            if self.spam_task:
                self.spam_task.cancel()
            await self.highrise.chat("🛑 اسپم متوقف شد!")
        else:
            await self.highrise.chat("⚠️ اسپمی فعال نیست")

    # ══════════════════════════════════════════
    #  ── تلپورت لوکیشن ──
    # ══════════════════════════════════════════
    async def _cmd_save_location(self, user: User, name: str):
        if not name:
            await self.highrise.chat("❌ نام لوکیشن بزن! مثال: !save home")
            return
        pos = await self._get_user_pos(user.id)
        if pos:
            self.locations[name.lower()] = {"x": pos.x, "y": pos.y, "z": pos.z, "facing": pos.facing}
            self._save_data()
            await self.highrise.chat(f"📍 لوکیشن '{name}' ذخیره شد!")
        else:
            await self.highrise.chat("❌ نتونستم موقعیتت رو بگیرم")

    async def _cmd_tp_to_location(self, user: User, name: str):
        if not name:
            await self.highrise.chat("❌ نام لوکیشن بزن")
            return
        key = name.lower()
        # چک طبقه
        if key in FLOOR_ALIASES:
            key = FLOOR_ALIASES[key]
            if key in self.floor_locations:
                pos = self._dict_to_pos(self.floor_locations[key])
                await self.highrise.teleport(user.id, pos)
                await self.highrise.chat(f"✨ {user.username} → {name}")
                return
        # چک لوکیشن
        if key in self.locations:
            pos = self._dict_to_pos(self.locations[key])
            await self.highrise.teleport(user.id, pos)
            await self.highrise.chat(f"✨ {user.username} → {name}")
        else:
            await self.highrise.chat(f"❌ لوکیشن '{name}' پیدا نشد")

    async def _cmd_set_floor(self, user: User, floor_key: str):
        if not floor_key:
            await self.highrise.chat("❌ مثال: !setfloor f1")
            return
        pos = await self._get_user_pos(user.id)
        if pos:
            canonical = FLOOR_ALIASES.get(floor_key.lower(), floor_key.lower())
            self.floor_locations[canonical] = {"x": pos.x, "y": pos.y, "z": pos.z, "facing": pos.facing}
            self._save_data()
            await self.highrise.chat(f"🏢 طبقه '{floor_key}' ذخیره شد! (کلید: {canonical})")
        else:
            await self.highrise.chat("❌ نتونستم موقعیتت رو بگیرم")

    async def _cmd_set_spot(self, user: User, name: str):
        if not name:
            await self.highrise.chat("❌ نام اسپات بزن! مثال: !setspot main")
            return
        pos = await self._get_user_pos(user.id)
        if pos:
            self.admin_spots[name.lower()] = {"x": pos.x, "y": pos.y, "z": pos.z, "facing": pos.facing}
            self._save_data()
            await self.highrise.chat(f"📍 اسپات '{name}' ذخیره شد!")
        else:
            await self.highrise.chat("❌ نتونستم موقعیتت رو بگیرم")

    async def _cmd_go_spot(self, user: User, name: str):
        key = name.lower()
        if key in self.admin_spots:
            pos = self._dict_to_pos(self.admin_spots[key])
            await self.highrise.walk_to(pos)
            await self.highrise.chat(f"🚶 بات رفت به اسپات '{name}'")
        else:
            spots = ", ".join(self.admin_spots.keys()) or "هیچ"
            await self.highrise.chat(f"❌ اسپات '{name}' نیست! اسپات‌ها: {spots}")

    # ══════════════════════════════════════════
    #  ── تلپورت همه ──
    # ══════════════════════════════════════════
    async def _cmd_tpall(self, user: User, location_name: str):
        key = location_name.lower()
        pos = None
        if key in FLOOR_ALIASES:
            fk = FLOOR_ALIASES[key]
            if fk in self.floor_locations:
                pos = self._dict_to_pos(self.floor_locations[fk])
        if not pos and key in self.locations:
            pos = self._dict_to_pos(self.locations[key])
        if not pos:
            await self.highrise.chat(f"❌ لوکیشن '{location_name}' پیدا نشد")
            return
        try:
            room_users = await self.highrise.get_room_users()
            count = 0
            for u, _ in room_users.content:
                try:
                    await self.highrise.teleport(u.id, pos)
                    count += 1
                    await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"tpall user error: {e}")
            await self.highrise.chat(f"✨ {count} نفر تلپورت شدن به {location_name}!")
        except Exception as e:
            await self.highrise.chat(f"❌ خطا: {e}")

    # ══════════════════════════════════════════
    #  ── بردن کنار خودم ──
    # ══════════════════════════════════════════
    async def _cmd_bring(self, requester: User, target_raw: str):
        target_name = target_raw.replace("@", "")
        if not target_name:
            await self.highrise.chat("❌ مثال: !bring @username")
            return
        admin_pos = await self._get_user_pos(requester.id)
        if not admin_pos:
            await self.highrise.chat("❌ نتونستم موقعیتت رو پیدا کنم")
            return
        target_id = await self._find_user_id(target_name)
        if target_id:
            await self.highrise.teleport(target_id, admin_pos)
            await self.highrise.chat(f"✨ @{target_name} آورده شد!")
        else:
            await self.highrise.chat(f"❌ @{target_name} توی روم نیست")

    # ══════════════════════════════════════════
    #  ── رفتن پیش کاربر ──
    # ══════════════════════════════════════════
    async def _cmd_goto(self, requester: User, target_raw: str):
        target_name = target_raw.replace("@", "")
        if not target_name:
            await self.highrise.chat("❌ مثال: !goto @username")
            return
        try:
            room_users = await self.highrise.get_room_users()
            for u, pos in room_users.content:
                if u.username.lower() == target_name.lower():
                    await self.highrise.walk_to(pos)
                    await self.highrise.chat(f"🚶 دارم میام پیش @{target_name}!")
                    return
            await self.highrise.chat(f"❌ @{target_name} توی روم نیست")
        except Exception as e:
            await self.highrise.chat(f"❌ خطا: {e}")

    # ══════════════════════════════════════════
    #  ── انتقال بات ──
    # ══════════════════════════════════════════
    async def _cmd_move_bot(self, user: User, location_name: str):
        key = location_name.lower()
        pos = None
        if key in FLOOR_ALIASES:
            fk = FLOOR_ALIASES[key]
            if fk in self.floor_locations:
                pos = self._dict_to_pos(self.floor_locations[fk])
        if not pos and key in self.locations:
            pos = self._dict_to_pos(self.locations[key])
        if not pos and key in self.admin_spots:
            pos = self._dict_to_pos(self.admin_spots[key])
        if pos:
            await self.highrise.walk_to(pos)
            await self.highrise.chat(f"🤖 بات رفت به {location_name}")
        else:
            await self.highrise.chat(f"❌ لوکیشن '{location_name}' پیدا نشد")

    # ══════════════════════════════════════════
    #  ── تلپورت خودکار بات ──
    # ══════════════════════════════════════════
    async def _cmd_auto_tp_on(self, user: User):
        pos = await self._get_user_pos(user.id)
        if pos:
            self.auto_tp_position = {"x": pos.x, "y": pos.y, "z": pos.z, "facing": pos.facing}
            self.auto_tp_enabled = True
            if self.auto_tp_task:
                self.auto_tp_task.cancel()
            self.auto_tp_task = asyncio.create_task(self._auto_tp_loop())
            await self.highrise.chat("✅ تلپورت خودکار بات فعال شد! بات هر ۵ثانیه به این موقعیت برمیگرده")
        else:
            await self.highrise.chat("❌ نتونستم موقعیتت رو بگیرم")

    async def _cmd_auto_tp_off(self):
        self.auto_tp_enabled = False
        if self.auto_tp_task:
            self.auto_tp_task.cancel()
            self.auto_tp_task = None
        await self.highrise.chat("🔴 تلپورت خودکار بات غیرفعال شد!")

    async def _auto_tp_loop(self):
        try:
            while self.auto_tp_enabled and self.auto_tp_position:
                await asyncio.sleep(5)
                try:
                    pos = self._dict_to_pos(self.auto_tp_position)
                    await self.highrise.walk_to(pos)
                except Exception as e:
                    print(f"auto_tp error: {e}")
        except asyncio.CancelledError:
            pass

    # ══════════════════════════════════════════
    #  ── فالو ──
    # ══════════════════════════════════════════
    async def _cmd_follow_start(self, user: User, target_raw: str):
        target_name = target_raw.replace("@", "")
        target_id = await self._find_user_id(target_name)
        if target_id:
            self.follow_target_id = target_id
            if self.follow_task:
                self.follow_task.cancel()
            self.follow_task = asyncio.create_task(self._follow_loop(target_id, target_name))
            await self.highrise.chat(f"🚶‍♂️ بات داره دنبال @{target_name} میره!")
        else:
            await self.highrise.chat(f"❌ @{target_name} توی روم نیست")

    async def _follow_loop(self, target_id: str, target_name: str):
        try:
            while True:
                await asyncio.sleep(2)
                try:
                    room_users = await self.highrise.get_room_users()
                    for u, pos in room_users.content:
                        if u.id == target_id:
                            await self.highrise.walk_to(pos)
                            break
                except Exception as e:
                    print(f"follow_loop error: {e}")
        except asyncio.CancelledError:
            pass

    async def _cmd_follow_stop(self):
        self.follow_target_id = None
        if self.follow_task:
            self.follow_task.cancel()
            self.follow_task = None
        await self.highrise.chat("⛔ فالو متوقف شد")

    # ══════════════════════════════════════════
    #  ── فریز (زندان) ──
    # ══════════════════════════════════════════
    async def _cmd_freeze(self, user: User, target_raw: str):
        target_name = target_raw.replace("@", "")
        target_id = await self._find_user_id(target_name)
        if not target_id:
            await self.highrise.chat(f"❌ @{target_name} توی روم نیست")
            return
        if target_id in self.frozen_users:
            await self.highrise.chat(f"⚠️ @{target_name} قبلاً فریزه")
            return
        # دریافت موقعیت فعلی
        pos = await self._get_user_pos(target_id)
        if not pos:
            await self.highrise.chat("❌ نتونستم موقعیت کاربر رو بگیرم")
            return
        task = asyncio.create_task(self._freeze_loop(target_id, pos))
        self.frozen_users[target_id] = task
        await self.highrise.chat(f"❄️ @{target_name} فریز شد! (زندانی)")

    async def _freeze_loop(self, user_id: str, pos: Position):
        try:
            while True:
                await self.highrise.teleport(user_id, pos)
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"freeze_loop error: {e}")

    async def _cmd_unfreeze(self, user: User, target_raw: str):
        target_name = target_raw.replace("@", "")
        # پیدا کردن ID از فریز‌شده‌ها
        target_id = await self._find_user_id(target_name)
        if target_id and target_id in self.frozen_users:
            self.frozen_users[target_id].cancel()
            del self.frozen_users[target_id]
            await self.highrise.chat(f"✅ @{target_name} آزاد شد!")
        else:
            await self.highrise.chat(f"❌ @{target_name} فریز نیست")

    # ══════════════════════════════════════════
    #  ── پرواز (گاوش) ──
    # ══════════════════════════════════════════
    async def _cmd_fly(self, user: User, target_raw: str, enable: bool):
        target_name = target_raw.replace("@", "")
        target_id = await self._find_user_id(target_name)
        if not target_id:
            await self.highrise.chat(f"❌ @{target_name} توی روم نیست")
            return
        if enable:
            if target_id in self.flying_users:
                await self.highrise.chat(f"⚠️ @{target_name} قبلاً داره پرواز می‌کنه!")
                return
            task = asyncio.create_task(self._fly_loop(target_id))
            self.flying_users[target_id] = task
            await self.highrise.chat(f"🕊️ @{target_name} الان داره پرواز می‌کنه! (گاوش)")
        else:
            if target_id in self.flying_users:
                self.flying_users[target_id].cancel()
                del self.flying_users[target_id]
                await self.highrise.chat(f"✅ @{target_name} از پرواز برگشت!")
            else:
                await self.highrise.chat(f"❌ @{target_name} در حال پرواز نیست")

    async def _fly_loop(self, user_id: str):
        """پرواز: ارسال متناوب emote-gravity + تلپورت به هوا"""
        try:
            while True:
                # ارسال دنس gravity
                await self.highrise.send_emote("emote-gravity", user_id)
                await asyncio.sleep(3)
                # تلپورت به بالا
                try:
                    pos = await self._get_user_pos(user_id)
                    if pos:
                        fly_pos = Position(x=pos.x, y=pos.y + 2.0, z=pos.z, facing=pos.facing)
                        await self.highrise.teleport(user_id, fly_pos)
                except Exception:
                    pass
                await asyncio.sleep(6)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"fly_loop error: {e}")

    # ══════════════════════════════════════════
    #  ── تیپ گلد ──
    # ══════════════════════════════════════════
    async def _cmd_tip_all(self, user: User, msg: str):
        parts = msg.split()
        amount_str = parts[1] if len(parts) > 1 else "1"
        try:
            amount = int(amount_str) if amount_str.isdigit() else 1
        except:
            amount = 1
        try:
            wallet = await self.highrise.get_wallet()
            bot_gold = 0
            for item in wallet.content:
                if item.type == "gold":
                    bot_gold = item.amount
                    break
            room_users = await self.highrise.get_room_users()
            eligible = [u for u, _ in room_users.content]
            total_needed = amount * len(eligible)
            if bot_gold < total_needed:
                await self.highrise.chat(f"❌ گلد کافی نیست! موجودی: {bot_gold} | نیاز: {total_needed}")
                return
            count = 0
            for ru in eligible:
                try:
                    bar_id, bar_val = get_tip_bar(amount)
                    remaining = amount
                    while remaining > 0:
                        use_bar_id, use_bar_val = get_tip_bar(remaining)
                        await self.highrise.tip_user(ru.id, use_bar_id)
                        remaining -= use_bar_val
                    count += 1
                    await asyncio.sleep(0.2)
                except Exception as te:
                    print(f"tip error: {te}")
            await self.highrise.chat(f"💰 به {count} نفر {amount} گلد تیپ داده شد!")
        except Exception as e:
            await self.highrise.chat(f"❌ خطا در تیپ: {e}")

    async def _cmd_tip_user(self, user: User, arg: str):
        parts = arg.split()
        if len(parts) < 2:
            await self.highrise.chat("❌ مثال: !tip @username 100")
            return
        target_name = parts[0].replace("@", "")
        try:
            amount = int(parts[1])
        except:
            amount = 1
        try:
            wallet = await self.highrise.get_wallet()
            bot_gold = 0
            for item in wallet.content:
                if item.type == "gold":
                    bot_gold = item.amount
                    break
            if bot_gold < amount:
                await self.highrise.chat(f"❌ گلد کافی نیست! موجودی: {bot_gold}")
                return
            target_id = await self._find_user_id(target_name)
            if not target_id:
                await self.highrise.chat(f"❌ @{target_name} توی روم نیست")
                return
            remaining = amount
            while remaining > 0:
                use_bar_id, use_bar_val = get_tip_bar(remaining)
                await self.highrise.tip_user(target_id, use_bar_id)
                remaining -= use_bar_val
            await self.highrise.chat(f"💰 {amount} گلد به @{target_name} تیپ داده شد!")
        except Exception as e:
            await self.highrise.chat(f"❌ خطا: {e}")

    # ══════════════════════════════════════════
    #  ── لباس ──
    # ══════════════════════════════════════════
    async def _cmd_copy_outfit(self, user: User):
        """کپی لباس بات از کاربر (با API)"""
        await self.highrise.chat(f"👗 در حال کپی لباس @{user.username}...")
        # در SDK جاری، get_user_outfit با آیدی کار می‌کنه
        # ما از get_my_outfit استفاده می‌کنیم و لباس فری پوشیم
        try:
            my_outfit = await self.highrise.get_my_outfit()
            if my_outfit and hasattr(my_outfit, 'outfit'):
                free_items = [
                    Item(type=it.type, id=it.id, amount=1, account_bound=False)
                    for it in my_outfit.outfit
                    if hasattr(it, 'account_bound') and not it.account_bound
                ]
                if free_items:
                    await self.highrise.set_outfit(free_items)
                    await self.highrise.chat(f"✅ لباس بات کپی شد ({len(free_items)} آیتم)!")
                else:
                    await self.highrise.chat("⚠️ آیتم فری برای کپی پیدا نشد")
            else:
                await self.highrise.chat("❌ نتونستم لباس بگیرم")
        except Exception as e:
            await self.highrise.chat(f"❌ خطا: {e}")

    async def _cmd_wear_user_outfit(self, user: User, target_raw: str, free_only: bool = False):
        """
        کپی کامل لباس یه کاربر (شامل کالکشن) و پوشیدن روی بات.
        free_only=True → فقط آیتم‌های غیر account_bound (رایگان/خریداری‌شده‌ی بات)
        """
        target_name = target_raw.replace("@", "").strip()
        if not target_name:
            await self.highrise.chat("❌ مثال: !wearoutfit @username")
            return

        await self.highrise.chat(f"👗 در حال گرفتن لباس @{target_name}...")

        # پیدا کردن آیدی کاربر در روم
        target_id = await self._find_user_id(target_name)
        if not target_id:
            await self.highrise.chat(f"❌ @{target_name} توی روم نیست")
            return

        try:
            # دریافت لباس کاربر از SDK
            outfit_resp = await self.highrise.get_user_outfit(target_id)

            if not outfit_resp or not hasattr(outfit_resp, 'outfit'):
                await self.highrise.chat("❌ نتونستم لباس رو بگیرم")
                return

            raw_items = outfit_resp.outfit

            if free_only:
                # فقط آیتم‌هایی که account_bound نیستن (رایگان / کالکشن عمومی)
                items = [
                    Item(type=it.type, id=it.id, amount=1,
                         account_bound=False, active_palette=getattr(it, 'active_palette', -1))
                    for it in raw_items
                    if not getattr(it, 'account_bound', False)
                ]
                mode_label = "رایگان"
            else:
                # همه آیتم‌ها — شامل کالکشن (account_bound=True)
                # بات باید مالک اون آیتم‌ها باشه، وگرنه SDK خطا میده
                items = [
                    Item(type=it.type, id=it.id, amount=1,
                         account_bound=getattr(it, 'account_bound', False),
                         active_palette=getattr(it, 'active_palette', -1))
                    for it in raw_items
                ]
                mode_label = "کامل (کالکشن)"

            if not items:
                await self.highrise.chat(f"⚠️ هیچ آیتمی برای پوشیدن پیدا نشد")
                return

            await self.highrise.set_outfit(items)
            await self.highrise.chat(
                f"✅ لباس {mode_label} @{target_name} پوشیده شد! "
                f"({len(items)} آیتم)"
            )

        except Exception as e:
            err = str(e)
            if "not owned" in err.lower() or "forbidden" in err.lower():
                await self.highrise.chat(
                    f"⚠️ بعضی آیتم‌های کالکشن @{target_name} مال بات نیست!\n"
                    f"از !wearfree @{target_name} بزن تا فقط آیتم‌های قابل پوشیدن بپوشه."
                )
            else:
                await self.highrise.chat(f"❌ خطا: {err}")

    async def _cmd_change_outfit(self, user: User, arg: str):
        try:
            n = int(arg.strip())
            if 1 <= n <= len(DEFAULT_OUTFITS):
                await self.highrise.set_outfit(DEFAULT_OUTFITS[n - 1])
                await self.highrise.chat(f"👗 لباس شماره {n} پوشیده شد!")
            else:
                await self.highrise.chat(f"❌ شماره لباس بین 1 تا {len(DEFAULT_OUTFITS)} باشه")
        except ValueError:
            await self.highrise.chat(f"❌ مثال: !outfit 1")

    # ══════════════════════════════════════════
    #  ── بازی تاس ──
    # ══════════════════════════════════════════
    async def _cmd_dice(self, user: User):
        result = random.randint(1, 6)
        faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        await self.highrise.chat(f"🎲 {user.username} تاس زد: {faces[result]} ({result})")

    async def _cmd_roll(self, user: User, msg: str):
        parts = msg.split()
        max_n = 6
        if len(parts) > 1 and parts[1].isdigit():
            max_n = max(2, int(parts[1]))
        result = random.randint(1, max_n)
        await self.highrise.chat(f"🎲 {user.username} عدد زد: {result} (از 1 تا {max_n})")

    # ══════════════════════════════════════════
    #  ── لیست دنس‌ها ──
    # ══════════════════════════════════════════
    async def _cmd_list_dances(self):
        lines = [f"{i}. {e.name}" for i, e in self.emotes_by_index.items()]
        chunk_size = 30
        for i in range(0, len(lines), chunk_size):
            await self.highrise.chat("\n".join(lines[i:i+chunk_size]))
            await asyncio.sleep(1.5)

    # ══════════════════════════════════════════
    #  ── وضعیت ──
    # ══════════════════════════════════════════
    async def _cmd_status(self):
        try:
            wallet = await self.highrise.get_wallet()
            gold = 0
            for item in wallet.content:
                if item.type == "gold":
                    gold = item.amount
                    break
        except:
            gold = "?"
        status = (
            f"🤖 وضعیت بات:\n"
            f"💰 گلد: {gold}\n"
            f"📢 اسپم: {'✅' if self.spam_active else '❌'}\n"
            f"👋 خوشامد: {'✅' if self.welcome_enabled else '❌'}\n"
            f"👋 خداحافظی: {'✅' if self.goodbye_enabled else '❌'}\n"
            f"🎵 دنس: {'✅' if self.dance_enabled else '❌'}\n"
            f"🌀 اتوتلپ: {'✅' if self.auto_tp_enabled else '❌'}\n"
            f"🚶 فالو: {'✅ فعال' if self.follow_task and not self.follow_task.done() else '❌'}\n"
            f"❄️ فریزشده: {len(self.frozen_users)} نفر\n"
            f"🎭 دنس بات: {'✅ ' + self.bot_dance_emote if self.bot_dance_task and not self.bot_dance_task.done() else '❌'}\n"
            f"👥 کل بازدید: {self.total_visitors}"
        )
        await self.highrise.chat(status)

    # ══════════════════════════════════════════
    #  ── ابزارها ──
    # ══════════════════════════════════════════
    async def _get_user_pos(self, user_id: str) -> Optional[Position]:
        try:
            room_users = await self.highrise.get_room_users()
            for u, pos in room_users.content:
                if u.id == user_id:
                    return pos
            return None
        except Exception as e:
            print(f"get_user_pos error: {e}")
            return None

    async def _find_user_id(self, username: str) -> Optional[str]:
        try:
            room_users = await self.highrise.get_room_users()
            for u, _ in room_users.content:
                if u.username.lower() == username.lower():
                    return u.id
            return None
        except Exception as e:
            print(f"find_user_id error: {e}")
            return None

    def _dict_to_pos(self, d: dict) -> Position:
        return Position(
            x=float(d.get("x", 0)),
            y=float(d.get("y", 0)),
            z=float(d.get("z", 0)),
            facing=d.get("facing", "FrontRight")
        )


# ══════════════════════════════════════════════
#  اجرای بات
# ══════════════════════════════════════════════
def run_bot_instance():
    if not ROOM_ID or not HIGHRISE_API_TOKEN:
        print("❌ ROOM_ID یا HIGHRISE_API_TOKEN تنظیم نشده!")
        print("فایل tiba.py رو چک کن")
        return
    print(f"🚀 بات در حال راه‌اندازی... | روم: {ROOM_ID[:8]}... | مالک: {OWNER_USERNAME}")
    bot = HiRiseBot()
    bot_def = BotDefinition(bot, ROOM_ID, HIGHRISE_API_TOKEN)
    asyncio.run(run_bot([bot_def]))


if __name__ == "__main__":
    start_keep_alive()
    run_bot_instance()
