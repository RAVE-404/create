# -*- coding: utf-8 -*-
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import sqlite3
from datetime import datetime, timedelta
import os
import time
import threading
import subprocess
import requests
import random
import string

# ==========================================
# BOT TOKEN
# ==========================================
TOKEN = "8931033773:AAHi6pr24UkclQ2cKokXnQn5eGRKn5NZyQw"

# ==========================================
# OWNER / ADMINS
# ==========================================
OWNER_ID = 5814450434
ADMINS = [5814450434]

# ==========================================
# WAITING LISTS
# ==========================================

WAITING_FEEDBACK = set()

# ==========================================
# BOT
# ==========================================
bot = telebot.TeleBot(TOKEN)

# ==========================================
# DATABASE
# ==========================================
conn = sqlite3.connect(
    "bot.db",
    check_same_thread=False
)

cursor = conn.cursor()

# ==========================================
# CREATE TABLES
# ==========================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER,
    expire TEXT,
    plan TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS keys(
    key TEXT,
    expire TEXT,
    used INTEGER
)
""")

conn.commit()

# ==========================================
# RESELLER TABLE
# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS resellers(
    user_id INTEGER,
    credits INTEGER
)
""")

conn.commit()

# ==========================================
# CHECK RESELLER
# ==========================================

def is_reseller(user_id):

    cursor.execute(
        "SELECT * FROM resellers WHERE user_id=?",
        (user_id,)
    )

    data = cursor.fetchone()

    if data:
        return True

    return False

# ==========================================
# GET RESELLER CREDITS
# ==========================================

def get_credits(user_id):

    cursor.execute(
        "SELECT credits FROM resellers WHERE user_id=?",
        (user_id,)
    )

    data = cursor.fetchone()

    if data:
        return data[0]

    return 0

# ==========================================
# ADD RESELLER
# ==========================================

@bot.message_handler(commands=['addreseller'])
def add_reseller(message):

    if message.chat.id not in ADMINS:

        bot.send_message(
            message.chat.id,
            "ADMIN ONLY"
        )

        return

    try:

        cmd = message.text.split()

        user_id = int(cmd[1])

        credits = int(cmd[2])

    except:

        bot.send_message(
            message.chat.id,
            """
USAGE :

/addreseller USER_ID CREDITS

EXAMPLE :

/addreseller 123456789 50
"""
        )

        return

    cursor.execute(
        "SELECT * FROM resellers WHERE user_id=?",
        (user_id,)
    )

    check = cursor.fetchone()

    if check:

        bot.send_message(
            message.chat.id,
            "USER ALREADY RESELLER"
        )

        return

    cursor.execute(
        "INSERT INTO resellers VALUES(?,?)",
        (
            user_id,
            credits
        )
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        f"""
 RESELLER ADDED

 USER ID :
{user_id}

 CREDITS :
{credits}
"""
    )

# ==========================================
# REMOVE RESELLER
# ==========================================

@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):

    if message.chat.id not in ADMINS:
        return

    try:

        user_id = int(
            message.text.split()[1]
        )

    except:

        bot.send_message(
            message.chat.id,
            "USAGE : /removereseller USER_ID"
        )

        return

    cursor.execute(
        "DELETE FROM resellers WHERE user_id=?",
        (user_id,)
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        " RESELLER REMOVED"
    )

# ==========================================
# ADD CREDITS
# ==========================================

@bot.message_handler(commands=['addcredits'])
def add_credits(message):

    if message.chat.id not in ADMINS:
        return

    try:

        cmd = message.text.split()

        user_id = int(cmd[1])

        credits = int(cmd[2])

    except:

        bot.send_message(
            message.chat.id,
            """
USAGE :

/addcredits USER_ID AMOUNT
"""
        )

        return

    cursor.execute(
        """
UPDATE resellers
SET credits = credits + ?
WHERE user_id=?
""",
        (
            credits,
            user_id
        )
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        f"""
 CREDITS ADDED

 USER :
{user_id}

 ADDED :
{credits}
"""
    )

# ==========================================
# MY CREDITS
# ==========================================

@bot.message_handler(commands=['credits'])
def credits(message):

    if not is_reseller(message.chat.id):

        bot.send_message(
            message.chat.id,
            "YOU ARE NOT RESELLER"
        )

        return

    total = get_credits(
        message.chat.id
    )

    bot.send_message(
        message.chat.id,
        f"""
 RESELLER PANEL

YOUR CREDITS :
{total}
"""
    )

# ==========================================
# RESELLER GENERATE KEY
# ==========================================

@bot.message_handler(commands=['rkey'])
def reseller_key(message):

    if not is_reseller(message.chat.id):

        bot.send_message(
            message.chat.id,
            "RESELLER ONLY"
        )

        return

    try:

        cmd = message.text.split()

        plan = cmd[1].lower()

    except:

        bot.send_message(
            message.chat.id,
            """
USAGE :

/rkey PLAN

PLANS :

1d
3d
30d
1y
lifetime
"""
        )

        return

    # ==========================================
    # PLAN PRICES
    # ==========================================

    prices = {

        "1d": 1,
        "3d": 4,
        "30d": 7,
        "1y": 8,
        "lifetime": 10

    }

    # ==========================================
    # CHECK VALID PLAN
    # ==========================================

    if plan not in prices:

        bot.send_message(
            message.chat.id,
            "INVALID PLAN"
        )

        return

    # ==========================================
    # CREDIT COST
    # ==========================================

    need_credits = prices[plan]

    # ==========================================
    # GET USER CREDITS
    # ==========================================

    credits = get_credits(
        message.chat.id
    )

    # ==========================================
    # CHECK ENOUGH CREDITS
    # ==========================================

    if credits < need_credits:

        bot.send_message(
            message.chat.id,
            f"""
 NOT ENOUGH CREDITS

 YOUR CREDITS :
{credits}

 REQUIRED :
{need_credits}
"""
        )

        return

    # ==========================================
    # GENERATE KEY
    # ==========================================

    key = generate_random_key()

    # ==========================================
    # PLAN SYSTEM
    # ==========================================

    if plan == "1d":

        expire = datetime.now() + timedelta(days=1)

    elif plan == "3d":

        expire = datetime.now() + timedelta(days=3)

    elif plan == "30d":

        expire = datetime.now() + timedelta(days=30)

    elif plan == "1y":

        expire = datetime.now() + timedelta(days=365)

    elif plan == "lifetime":

        expire = "lifetime"

    # ==========================================
    # SAVE KEY
    # ==========================================

    cursor.execute(
        "INSERT INTO keys VALUES(?,?,?)",
        (
            key,
            str(expire),
            0
        )
    )

    # ==========================================
    # DEDUCT CREDITS
    # ==========================================

    cursor.execute(
        """
UPDATE resellers
SET credits = credits - ?
WHERE user_id=?
""",
        (
            need_credits,
            message.chat.id
        )
    )

    conn.commit()

    # ==========================================
    # REMAINING CREDITS
    # ==========================================

    remaining = credits - need_credits

    # ==========================================
    # SEND KEY
    # ==========================================

    bot.send_message(
        message.chat.id,
        f"""
 RESELLER KEY GENERATED

 KEY :
{key}

 PLAN :
{plan}

 DEDUCTED :
{need_credits}

 REMAINING :
{remaining}
"""
    )

# ==========================================
# RESELLERS LIST
# ==========================================

@bot.message_handler(commands=['resellers'])
def reseller_list(message):

    if message.chat.id not in ADMINS:
        return

    cursor.execute(
        "SELECT * FROM resellers"
    )

    data = cursor.fetchall()

    if not data:

        bot.send_message(
            message.chat.id,
            "NO RESELLERS FOUND"
        )

        return

    text = " RESELLERS LIST\n\n"

    for user in data:

        text += f" USER : {user[0]}\n"
        text += f" CREDITS : {user[1]}\n\n"

    bot.send_message(
        message.chat.id,
        text
    )

# ==========================================
# AUTO CLEAN EXPIRED USERS
# ==========================================

def clean_expired():

    while True:

        now = datetime.now()

        cursor.execute(
            "SELECT user_id, expire FROM users"
        )

        data = cursor.fetchall()

        for user_id, expire in data:

            if expire != "lifetime":

                ex = datetime.fromisoformat(expire)

                if now > ex:

                    cursor.execute(
                        "DELETE FROM users WHERE user_id=?",
                        (user_id,)
                    )

        conn.commit()

        time.sleep(60)  # CHECK EVERY 60 SECONDS


threading.Thread(
    target=clean_expired,
    daemon=True
).start()

# ==========================================
# ACCESS CHECK
# ==========================================
def has_access(user_id):

    if user_id in ADMINS:
        return True

    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    data = cursor.fetchone()

    if data:
        return True

    return False

# ==========================================
# SAVE LOGS
# ==========================================
def save_log(text):

    with open("logs.txt", "a") as f:

        f.write(
            f"{datetime.now()} : {text}\n"
        )

# ==========================================
# START MENU
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):

    if not has_access(message.chat.id):

        bot.send_message(
            message.chat.id,
            """
NO ACTIVE SUBSCRIPTION

REDEEM A KEY FIRST

/redeem YOURKEY
            """
        )

        return

    menu = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    btn1 = KeyboardButton("1 - Spam Share")
    btn2 = KeyboardButton("2 - Auto Create")
    btn3 = KeyboardButton("3 - Cracking")
    btn4 = KeyboardButton("📁 Upload File")
    btn5 = KeyboardButton("👤 My Account")
    btn6 = KeyboardButton("📊 Status")
    btn7 = KeyboardButton("✉️ Message Admin")
    btn8 = KeyboardButton("📝 Feedback")
    btn9 = KeyboardButton("/stop")

    menu.row(btn1, btn2)
    menu.row(btn3, btn4)
    menu.row(btn5, btn6)
    menu.row(btn7, btn8)
    menu.row(btn9)

    bot.send_message(
        message.chat.id,
        """
WELCOME TO VIP TOOL BOT
        """,
        reply_markup=menu
    )

# ==========================================
# MY ACCOUNT
# ==========================================
@bot.message_handler(commands=['me'])
def my_account(message):

    cursor.execute(
        "SELECT expire, plan FROM users WHERE user_id=?",
        (message.chat.id,)
    )

    data = cursor.fetchone()

    if not data:

        if message.chat.id in ADMINS:

            bot.send_message(
                message.chat.id,
                """
OWNER ACCOUNT

PLAN : LIFETIME
                """
            )

            return

        bot.send_message(
            message.chat.id,
            "NO ACTIVE PLAN"
        )

        return

    expire, plan = data

    bot.send_message(
        message.chat.id,
        f"""
YOUR ACCOUNT

ID : {message.chat.id}

PLAN : {plan}

EXPIRE :
{expire}
        """
    )

# ==========================================
# GENERATE RANDOM KEY
# ==========================================
def generate_random_key():

    chars = string.ascii_uppercase + string.digits

    random_part = ''.join(
        random.choice(chars)
        for _ in range(12)
    )

    return f"VIP-{random_part}"

# ==========================================
# GENERATE KEY
# ==========================================
@bot.message_handler(commands=['genkey'])
def genkey(message):

    if message.chat.id not in ADMINS:

        bot.send_message(
            message.chat.id,
            "ADMIN ONLY"
        )

        return

    try:

        cmd = message.text.split()

        plan = cmd[1]

    except:

        bot.send_message(
            message.chat.id,
            """
USAGE :

/genkey PLAN

PLANS :
1m
5m
10m
30m
1d
3d
30d
1y
lifetime
            """
        )

        return

    # ==========================================
    # RANDOM KEY
    # ==========================================

    key = generate_random_key()

    # ==========================================
    # PLAN SYSTEM
    # ==========================================

    if plan == "1m":

        expire = datetime.now() + timedelta(minutes=1)

    elif plan == "5m":

        expire = datetime.now() + timedelta(minutes=5)
        
    elif plan == "10m":

        expire = datetime.now() + timedelta(minutes=10)
        
    elif plan == "30m":

        expire = datetime.now() + timedelta(minutes=30)

    elif plan == "1d":

        expire = datetime.now() + timedelta(days=1)

    elif plan == "3d":

        expire = datetime.now() + timedelta(days=3)

    elif plan == "30d":

        expire = datetime.now() + timedelta(days=30)

    elif plan == "1y":

        expire = datetime.now() + timedelta(days=365)

    elif plan == "lifetime":

        expire = "lifetime"

    else:

        bot.send_message(
            message.chat.id,
            "INVALID PLAN"
        )

        return

    # ==========================================
    # SAVE KEY
    # ==========================================

    cursor.execute(
        "INSERT INTO keys VALUES(?,?,?)",
        (
            key,
            str(expire),
            0
        )
    )

    conn.commit()

    # ==========================================
    # SUCCESS MESSAGE
    # ==========================================

    bot.send_message(
        message.chat.id,
        f"""
 KEY CREATED

 KEY :
{key}

 PLAN :
{plan}

 EXPIRE :
{expire}
        """
    )

# ==========================================
# REDEEM KEY
# ==========================================

@bot.message_handler(commands=['redeem'])
def redeem(message):

    try:

        key = message.text.split()[1]

    except:

        bot.send_message(
            message.chat.id,
            "USAGE : /redeem KEY"
        )

        return

    cursor.execute(
        "SELECT * FROM keys WHERE key=?",
        (key,)
    )

    data = cursor.fetchone()

    if not data:

        bot.send_message(
            message.chat.id,
            "INVALID KEY"
        )

        return

    key_name, expire, used = data

    if used == 1:

        bot.send_message(
            message.chat.id,
            "KEY ALREADY USED"
        )

        return

    cursor.execute(
        "INSERT INTO users VALUES(?,?,?)",
        (
            message.chat.id,
            expire,
            "VIP"
        )
    )

    cursor.execute(
        "UPDATE keys SET used=1 WHERE key=?",
        (key,)
    )

    conn.commit()

    # ==========================================
    # SEND NOTICE TO OWNER
    # ==========================================

    user = message.from_user

    bot.send_message(
        OWNER_ID,
        f"""
 KEY REDEEMED

 NAME : {user.first_name}

 USER ID : {user.id}

 USERNAME : @{user.username}

 KEY : {key}

 EXPIRE : {expire}
"""
    )

    # ==========================================
    # MESSAGE TO USER
    # ==========================================

    bot.send_message(
        message.chat.id,
        f"""
KEY ACTIVATED

EXPIRE :
{expire}
        """
    )

# ==========================================
# REMOVE KEY
# ==========================================
@bot.message_handler(commands=['removekey'])
def removekey(message):

    if message.chat.id not in ADMINS:
        return

    try:

        key = message.text.split()[1]

    except:

        bot.send_message(
            message.chat.id,
            "USAGE : /removekey KEY"
        )

        return

    cursor.execute(
        "DELETE FROM keys WHERE key=?",
        (key,)
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        f"KEY REMOVED : {key}"
    )

# ==========================================
# REVOKE USER
# ==========================================
@bot.message_handler(commands=['revoke'])
def revoke(message):

    if message.chat.id not in ADMINS:
        return

    try:

        user_id = message.text.split()[1]

    except:

        bot.send_message(
            message.chat.id,
            "USAGE : /revoke USER_ID"
        )

        return

    cursor.execute(
        "DELETE FROM users WHERE user_id=?",
        (user_id,)
    )

    conn.commit()

    bot.send_message(
        message.chat.id,
        "USER REVOKED"
    )

# ==========================================
# STATUS
# ==========================================
@bot.message_handler(commands=['status'])
def status(message):

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM keys"
    )

    total_keys = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM keys WHERE used=1"
    )

    used_keys = cursor.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"""
BOT STATUS

ACTIVE USERS : {total_users}
TOTAL KEYS : {total_keys}
USED KEYS : {used_keys}

BOT STATUS : ONLINE
        """
    )

# ==========================================
# USERS LIST
# ==========================================
@bot.message_handler(commands=['users'])
def users_list(message):

    if message.chat.id not in ADMINS:
        return

    cursor.execute(
        "SELECT * FROM users"
    )

    data = cursor.fetchall()

    if not data:

        bot.send_message(
            message.chat.id,
            "NO USERS FOUND"
        )

        return

    text = "ACTIVE USERS\n\n"

    for user in data:

        text += f"ID : {user[0]}\n"
        text += f"EXPIRE : {user[1]}\n"
        text += f"PLAN : {user[2]}\n\n"

    bot.send_message(
        message.chat.id,
        text
    )

# ==========================================
# KEYS LIST
# ==========================================
@bot.message_handler(commands=['keys'])
def keys_list(message):

    if message.chat.id not in ADMINS:
        return

    cursor.execute(
        "SELECT * FROM keys"
    )

    data = cursor.fetchall()

    if not data:

        bot.send_message(
            message.chat.id,
            "NO KEYS FOUND"
        )

        return

    text = "GENERATED KEYS\n\n"

    for key in data:

        text += f"KEY : {key[0]}\n"
        text += f"EXPIRE : {key[1]}\n"
        text += f"USED : {key[2]}\n\n"

    bot.send_message(
        message.chat.id,
        text
    )

# ==========================================
# BROADCAST
# ==========================================
@bot.message_handler(commands=['broadcast'])
def broadcast(message):

    if message.chat.id not in ADMINS:
        return

    # CHECK REPLY
    if not message.reply_to_message:

        bot.send_message(
            message.chat.id,
            """
USAGE :

Reply to a PHOTO or MESSAGE then type:

/broadcast
            """
        )

        return

    cursor.execute(
        "SELECT user_id FROM users"
    )

    users = cursor.fetchall()

    sent = 0
    failed = 0

    # ==========================================
    # PHOTO BROADCAST
    # ==========================================
    if message.reply_to_message.photo:

        photo = message.reply_to_message.photo[-1].file_id

        caption = message.reply_to_message.caption or ""

        for user in users:

            try:

                bot.send_photo(
                    user[0],
                    photo,
                    caption=f" ANNOUNCEMENT\n\n{caption}"
                )

                sent += 1

                time.sleep(0.3)

            except:

                failed += 1

                continue

    # ==========================================
    # TEXT BROADCAST
    # ==========================================
    else:

        text = message.reply_to_message.text

        for user in users:

            try:

                bot.send_message(
                    user[0],
                    f" ANNOUNCEMENT\n\n{text}"
                )

                sent += 1

                time.sleep(0.3)

            except:

                failed += 1

                continue

    bot.send_message(
        message.chat.id,
        f"""
 BROADCAST FINISHED

SUCCESS : {sent}
FAILED : {failed}
        """
    )

# ==========================================
# SHARE TOOL
# ==========================================

def get_share_link(message):

    post_link = message.text

    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )

    btn1 = KeyboardButton("1 COOKIE")
    btn2 = KeyboardButton("ALL COOKIES")

    markup.row(btn1, btn2)

    msg = bot.send_message(
        message.chat.id,
        "SELECT SHARE MODE",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        select_share_mode,
        post_link
    )

# ==========================================
# SELECT SHARE MODE
# ==========================================

def select_share_mode(message, post_link):

    mode = message.text

    msg = bot.send_message(
        message.chat.id,
        "HOW MANY SHARES?"
    )

    if mode == "1 COOKIE":

        bot.register_next_step_handler(
            msg,
            run_share_one,
            post_link
        )

    elif mode == "ALL COOKIES":

        bot.register_next_step_handler(
            msg,
            run_share_all,
            post_link
        )

    else:

        bot.send_message(
            message.chat.id,
            "INVALID MODE"
        )

# ==========================================
# SHARE USING 1 COOKIE
# ==========================================

def run_share_one(message, post_link):

    amount = message.text

    bot.send_message(
        message.chat.id,
        f"""
 SHARE STARTED

MODE : 1 COOKIE

LINK :
{post_link}

AMOUNT :
{amount}
        """
    )

    threading.Thread(
        target=lambda: os.system(
            f"python druu.py '{post_link}' '{amount}' '{message.chat.id}' one"
        )
    ).start()

# ==========================================
# SHARE USING ALL COOKIES
# ==========================================

def run_share_all(message, post_link):

    amount = message.text

    bot.send_message(
        message.chat.id,
        f"""
 SHARE STARTED

MODE : ALL COOKIES

LINK :
{post_link}

AMOUNT :
{amount}
        """
    )

    threading.Thread(
        target=lambda: os.system(
            f"python druu.py '{post_link}' '{amount}' '{message.chat.id}' all"
        )
    ).start()
     
# ==========================================
# ADD MANY COOKIES
# ==========================================

COOKIE_FILE = "cookies.txt"

@bot.message_handler(commands=['addcookie'])
def add_cookie(message):

    msg = bot.send_message(
        message.chat.id,
        """
SEND COOKIES

EXAMPLE :

cookie1
cookie2
cookie3
        """
    )

    bot.register_next_step_handler(
        msg,
        save_cookies
    )


def save_cookies(message):

    cookies = message.text.strip().splitlines()

    added = 0

    with open(COOKIE_FILE, "a") as f:

        for cookie in cookies:

            cookie = cookie.strip()

            if cookie:

                f.write(cookie + "\n")

                added += 1

    total = len(open(COOKIE_FILE).read().splitlines())

    bot.send_message(
        message.chat.id,
        f"""
 COOKIES ADDED

 ADDED : {added}
 TOTAL : {total}
        """
    )
    
# ==========================================
# LIST COOKIES
# ==========================================

@bot.message_handler(commands=['listcookie'])
def list_cookie(message):

    if not os.path.exists(COOKIE_FILE):

        bot.send_message(
            message.chat.id,
            " NO COOKIE FILE"
        )

        return

    cookies = open(COOKIE_FILE).read().splitlines()

    if len(cookies) == 0:

        bot.send_message(
            message.chat.id,
            " NO COOKIES SAVED"
        )

        return

    text = " COOKIE LIST\n\n"

    for i, cookie in enumerate(cookies, start=1):

        short = cookie[:50]

        text += f"{i}. {short}...\n\n"

    text += f" TOTAL : {len(cookies)}"

    bot.send_message(
        message.chat.id,
        text
    )
    
# ==========================================
# CHECK COOKIES
# ==========================================

@bot.message_handler(commands=['checkcookie'])
def check_cookie(message):

    if not os.path.exists(COOKIE_FILE):

        bot.send_message(
            message.chat.id,
            " NO COOKIE FILE"
        )

        return

    cookies = open(COOKIE_FILE).read().splitlines()

    if len(cookies) == 0:

        bot.send_message(
            message.chat.id,
            " NO COOKIES SAVED"
        )

        return

    live = 0
    dead = 0

    msg = bot.send_message(
        message.chat.id,
        " CHECKING COOKIES..."
    )

    for cookie in cookies:

        try:

            headers = {
                "cookie": cookie,
                "user-agent": "Mozilla/5.0"
            }

            r = requests.get(
                "https://mbasic.facebook.com/",
                headers=headers,
                timeout=10
            )

            if "save-device" in r.text or "facebook.com" in r.url:

                live += 1

            else:

                dead += 1

        except:

            dead += 1

    bot.edit_message_text(
        f"""
 COOKIE CHECK DONE

 LIVE : {live}
 DEAD : {dead}
 TOTAL : {len(cookies)}
        """,
        message.chat.id,
        msg.message_id
    )
    
# ==========================================
# REMOVE COOKIES
# ==========================================

@bot.message_handler(commands=['removecookie'])
def remove_cookie(message):

    if os.path.exists(COOKIE_FILE):

        os.remove(COOKIE_FILE)

        bot.send_message(
            message.chat.id,
            " ALL COOKIES REMOVED"
        )

    else:

        bot.send_message(
            message.chat.id,
            " NO COOKIE FILE FOUND"
        )

# ==========================================
# AUTO CREATE
# ==========================================

def auto_create(message):

    amount = message.text

    msg = bot.send_message(
        message.chat.id,
        "ENTER CUSTOM PASSWORD"
    )

    bot.register_next_step_handler(
        msg,
        auto_create_password,
        amount
    )

# ==========================================
# PASSWORD
# ==========================================

def auto_create_password(message, amount):

    password = message.text

    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )

    btn1 = KeyboardButton("RANDOM FULL NAME")
    btn2 = KeyboardButton("CUSTOM FIRST NAME")
    btn3 = KeyboardButton("CUSTOM LAST NAME")
    btn4 = KeyboardButton("FULL CUSTOM NAME")

    markup.row(btn1, btn2)
    markup.row(btn3, btn4)

    msg = bot.send_message(
        message.chat.id,
        "SELECT NAME MODE",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        auto_create_name_mode,
        amount,
        password
    )

# ==========================================
# NAME MODE
# ==========================================

def auto_create_name_mode(
    message,
    amount,
    password
):

    mode = message.text

    # RANDOM FULL NAME
    if mode == "RANDOM FULL NAME":

        bot.send_message(
            message.chat.id,
            f"""
AUTO CREATE STARTED

TOTAL :
{amount}

PASSWORD :
{password}

NAME MODE :
RANDOM FULL NAME
"""
        )

        threading.Thread(
            target=lambda: os.system(
                f"python autoc.py '{amount}' '{password}' '{message.chat.id}' '1'"
            )
        ).start()

    # CUSTOM FIRST NAME
    elif mode == "CUSTOM FIRST NAME":

        msg = bot.send_message(
            message.chat.id,
            "ENTER FIRST NAME"
        )

        bot.register_next_step_handler(
            msg,
            auto_create_custom_first,
            amount,
            password
        )

    # CUSTOM LAST NAME
    elif mode == "CUSTOM LAST NAME":

        msg = bot.send_message(
            message.chat.id,
            "ENTER LAST NAME"
        )

        bot.register_next_step_handler(
            msg,
            auto_create_custom_last,
            amount,
            password
        )

    # FULL CUSTOM NAME
    elif mode == "FULL CUSTOM NAME":

        msg = bot.send_message(
            message.chat.id,
            "ENTER FIRST NAME"
        )

        bot.register_next_step_handler(
            msg,
            auto_create_firstname,
            amount,
            password
        )

    else:

        bot.send_message(
            message.chat.id,
            "INVALID MODE"
        )

# ==========================================
# CUSTOM FIRST NAME
# ==========================================

def auto_create_custom_first(
    message,
    amount,
    password
):

    firstname = message.text

    bot.send_message(
        message.chat.id,
        f"""
AUTO CREATE STARTED

TOTAL :
{amount}

PASSWORD :
{password}

FIRST NAME :
{firstname}
"""
    )

    threading.Thread(
        target=lambda: os.system(
            f"python autoc.py '{amount}' '{password}' '{message.chat.id}' '2' '{firstname}'"
        )
    ).start()

# ==========================================
# CUSTOM LAST NAME
# ==========================================

def auto_create_custom_last(
    message,
    amount,
    password
):

    lastname = message.text

    bot.send_message(
        message.chat.id,
        f"""
AUTO CREATE STARTED

TOTAL :
{amount}

PASSWORD :
{password}

LAST NAME :
{lastname}
"""
    )

    threading.Thread(
        target=lambda: os.system(
            f"python autoc.py '{amount}' '{password}' '{message.chat.id}' '3' '{lastname}'"
        )
    ).start()

# ==========================================
# FIRST NAME
# ==========================================

def auto_create_firstname(
    message,
    amount,
    password
):

    firstname = message.text

    msg = bot.send_message(
        message.chat.id,
        "ENTER LAST NAME"
    )

    bot.register_next_step_handler(
        msg,
        auto_create_lastname,
        amount,
        password,
        firstname
    )

# ==========================================
# LAST NAME
# ==========================================

def auto_create_lastname(
    message,
    amount,
    password,
    firstname
):

    lastname = message.text

    bot.send_message(
        message.chat.id,
        f"""
AUTO CREATE STARTED

TOTAL :
{amount}

PASSWORD :
{password}

NAME :
{firstname} {lastname}
"""
    )

    threading.Thread(
        target=lambda: os.system(
            f"python autoc.py '{amount}' '{password}' '{message.chat.id}' '4' '{firstname}' '{lastname}'"
        )
    ).start()

# ==========================================
# CRACK TOOL
# ==========================================
def crack_tool(message):

    chat_id = message.chat.id

    # CHECK IF TEXT EXISTS
    if not message.text:

        bot.send_message(
            chat_id,
            " SEND THE FILE PATH ONLY"
        )

        return

    # GET FILE PATH
    file_path = message.text.strip()

    # CHECK FILE
    if not os.path.exists(file_path):

        bot.send_message(
            chat_id,
            " FILE NOT FOUND"
        )

        return

    # START MESSAGE
    bot.send_message(
        chat_id,
        f"""
 CRACK STARTED

 FILE:
{file_path}
        """
    )

    # START TOOL
    threading.Thread(
        target=lambda: os.system(
            f"python3 RV.py '{file_path}' '{chat_id}'"
        ),
        daemon=True
    ).start()


# ==========================================
# COMMAND HANDLER
# ==========================================
@bot.message_handler(commands=['crack'])
def crack_command(message):

    msg = bot.send_message(
        message.chat.id,
        " SEND FILE PATH"
    )

    bot.register_next_step_handler(
        msg,
        crack_tool
    )

# ==========================================
# FILE UPLOAD
# ==========================================
@bot.message_handler(content_types=['document'])
def handle_docs(message):

    if not has_access(message.chat.id):

        bot.send_message(
            message.chat.id,
            "NO ACTIVE SUBSCRIPTION"
        )

        return

    try:

        # GET FILE INFO
        file_info = bot.get_file(
            message.document.file_id
        )

        # DOWNLOAD FILE
        downloaded = bot.download_file(
            file_info.file_path
        )

        # CREATE DOWNLOAD FOLDER
        os.makedirs(
            "downloads",
            exist_ok=True
        )

        # FILE NAME
        file_name = message.document.file_name

        # FULL ABSOLUTE PATH
        path = os.path.abspath(
            f"downloads/{file_name}"
        )

        # SAVE FILE
        with open(path, 'wb') as new_file:

            new_file.write(downloaded)

        # SAVE LOG
        save_log(
            f"{message.chat.id} uploaded {path}"
        )

        # SUCCESS MESSAGE
        bot.send_message(
            message.chat.id,
            f"""
 FILE SAVED SUCCESSFULLY

 FULL PATH:
{path}



NOW PRESS:
3 - Cracking

THEN SEND THIS PATH:
{path}
            """
        )

    except Exception as e:

        bot.send_message(
            message.chat.id,
            f" ERROR:\n{e}"
        )

# ==========================================
# HELP MENU
# ==========================================

@bot.message_handler(commands=['help'])
def help_menu(message):

    bot.send_message(
        message.chat.id,
        """
USER COMMANDS

/start
/help
/me
/redeem KEY
/status
/stop
/addcookie
/listcookie
/checkcookie
/removecookie

RESELLER COMMANDS

/credits
/rkey PLAN

ADMIN COMMANDS

/genkey PLAN
/removekey KEY
/revoke USER_ID
/broadcast MESSAGE
/users
/keys

RESELLER ADMIN COMMANDS

/addreseller USER_ID CREDITS
/removereseller USER_ID
/addcredits USER_ID AMOUNT
/resellers

PLANS

1m
5m
10m
30m
1d
3d
30d
1y
lifetime
        """
    )

# ==========================================
# STOP
# ==========================================
@bot.message_handler(commands=['stop'])
def stop(message):

    os.system("pkill -f druu.py")
    os.system("pkill -f autoc.py")
    os.system("pkill -f RV.py")

    bot.send_message(
        message.chat.id,
        "ALL TASKS STOPPED"
    )

# ==========================================
# BUTTONS
# ==========================================
@bot.message_handler(func=lambda message: True)
def buttons(message):

    if message.chat.id in WAITING_FEEDBACK:
        return

    text = message.text.strip() if message.text else ""

    if not has_access(message.chat.id):

        bot.send_message(message.chat.id, "REDEEM A KEY FIRST")
        return


    # =========================
    # SPAM SHARE
    # =========================
    if text == "1 - Spam Share":

        msg = bot.send_message(message.chat.id, "SEND POST LINK")
        bot.register_next_step_handler(msg, get_share_link)
        return


    # =========================
    # AUTO CREATE
    # =========================
    elif text == "2 - Auto Create":

        msg = bot.send_message(message.chat.id, "HOW MANY ACCOUNTS?")
        bot.register_next_step_handler(msg, auto_create)
        return


    # =========================
    # CRACKING
    # =========================
    elif text == "3 - Cracking":

        msg = bot.send_message(
            message.chat.id,
            "UPLOAD FILE FIRST THEN SEND PATH"
        )

        bot.register_next_step_handler(msg, crack_tool)
        return


    # =========================
    # UPLOAD FILE
    # =========================
    elif text == "📁 Upload File":

        bot.send_message(message.chat.id, "SEND YOUR TXT FILE NOW")
        return


    # =========================
    # MY ACCOUNT
    # =========================
    elif text == "👤 My Account":

        my_account(message)
        return


    # =========================
    # STATUS
    # =========================
    elif text == "⚙️ Status":

        status(message)
        return


    # =========================
    # MESSAGE ADMIN (FIXED - NO CALL FUNCTION)
    # =========================
    elif text == "✉️ Message Admin":

        msg = bot.send_message(
            message.chat.id,
            "✉️ MESSAGE ADMIN\n\nSend your message now."
        )

        bot.register_next_step_handler(msg, receive_admin_message)
        return


    # =========================
    # FEEDBACK (FIXED - NO CALL FUNCTION)
    # =========================
    elif text == "📝 Feedback":

        WAITING_FEEDBACK.add(message.chat.id)

        bot.send_message(
            message.chat.id,
            "📝 FEEDBACK\n\nSend:\n- Text\n- Screenshot + Caption"
        )
        return


    # =========================
    # STOP
    # =========================
    elif text == "/stop":

        stop(message)
        return


    else:

        bot.send_message(message.chat.id, "PRESS /start")

# ==========================================
# FILE UPLOAD HANDLER
# ==========================================
@bot.message_handler(content_types=['document'])
def save_file(message):

    try:

        chat_id = message.chat.id

        # GET FILE INFO
        file_info = bot.get_file(
            message.document.file_id
        )

        # DOWNLOAD FILE
        downloaded = bot.download_file(
            file_info.file_path
        )

        # CREATE FOLDER
        os.makedirs(
            "downloads",
            exist_ok=True
        )

        # ORIGINAL FILE NAME
        file_name = message.document.file_name

        # SAVE PATH
        save_path = os.path.abspath(
            f"downloads/{file_name}"
        )

        # SAVE FILE
        with open(save_path, "wb") as f:
            f.write(downloaded)

        # SUCCESS
        bot.send_message(
            chat_id,
            f"""
 FILE SAVED SUCCESSFULLY

 PATH:
{save_path}



NOW PRESS:
3 - Cracking

THEN SEND THIS PATH:
{save_path}
            """
        )

    except Exception as e:

        bot.send_message(
            message.chat.id,
            f" ERROR:\n{e}"
        )
        
# ==========================================
# MESSAGE ADMIN
# ==========================================

def receive_admin_message(message):

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "No Username"
    )

    text = message.text if message.text else "Non-text message"

    bot.send_message(
        OWNER_ID,
        f"""
📩 NEW MESSAGE

👤 USER ID: {message.from_user.id}

🔰 USERNAME: {username}

📝 MESSAGE:
{text}
"""
    )

    bot.send_message(message.chat.id, "✅ Message sent to admin.")

# ==========================================
# FEEDBACK START
# ==========================================
@bot.message_handler(func=lambda m: m.text == "📝 Feedback")
def feedback_start(message):

    WAITING_FEEDBACK.add(message.chat.id)

    bot.send_message(
        message.chat.id,
        """
📝 FEEDBACK

Send:

- Text feedback
OR
- Screenshot + Caption

Your feedback will be sent directly to the admin.
"""
    )


# ==========================================
# HANDLE TEXT + PHOTO FEEDBACK
# ==========================================
@bot.message_handler(content_types=["text", "photo"])
def receive_feedback(message):

    if message.chat.id not in WAITING_FEEDBACK:
        return

    user_id = message.chat.id

    if message.content_type == "text":

        bot.send_message(
            ADMIN_CHAT_ID,
            f"📝 FEEDBACK\n\nFrom: {user_id}\n\n{message.text}"
        )

        bot.send_message(user_id, "✅ Thank you!")

    elif message.content_type == "photo":

        caption = message.caption if message.caption else "No caption"

        bot.send_photo(
            ADMIN_CHAT_ID,
            message.photo[-1].file_id,
            caption=f"📝 FEEDBACK\n\nFrom: {user_id}\n\n{caption}"
        )

        bot.send_message(user_id, "✅ Screenshot received!")

    WAITING_FEEDBACK.discard(user_id)
        
# ==========================================
# BOT START
# ==========================================
print("BOT IS RUNNING...")

while True:
    try:
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60
        )

    except Exception as e:
        print(e)
        time.sleep(5)
