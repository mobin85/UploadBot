import asyncio
from datetime import datetime, timedelta

from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.types.messages_and_media.message import Message
from pyrogram import Client, filters
from cryptography.fernet import Fernet
import pyromod.listen
from aiohttp import ClientSession

from key import KEY
from setting import *
from keyboard import *
from db import User, Links

cipher = Fernet(KEY)


async def human_readable(num, suffix="بایت"):
    for unit in ["", "کیلو", "مگا", "گیگا", "ترا", "پتا", "اکسا", "زتا"]:
        if abs(num) < 1024.0:
            return f"{num:3.2f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.2f} یوتابایت:"


async def show_time(time: datetime):
    hour, minute, second = time.hour, time.minute, time.second
    if hour and minute and second:
        return f"{hour} ساعت و {minute} دقیقه و {second} ثانیه"
    elif hour and minute:
        return f"{hour} ساعت و {minute} دقیقه"
    elif hour and second:
        return f"{hour} ساعت و {second} ثانیه"
    elif minute and second:
        return f"{minute} دقیقه و {second} ثانیه"
    elif hour:
        return f"{hour} ساعت"
    elif minute:
        return f"{minute} دقیقه"
    elif second:
        return f"{second} ثانیه"


class Bot(Client):
    async def check_time(self):
        while True:
            link: Links
            for link in Links.select():
                if (link.link_lifetime - datetime.now()).total_seconds() <= 0:
                    link.delete_instance()
                    link.save()

    def __init__(self):
        super().__init__("bot", API_ID, API_HASH, bot_token=TOKEN)
        self.running = False

        @self.on_message(filters=filters.private & filters.text)
        async def echo(_, msg: Message):
            if not self.running:
                self.running = True
                self.executor.submit(lambda: asyncio.run(self.check_time()))

            text = msg.text
            chat = msg.chat.id
            if text == "/start":
                await self.start_command(msg)

            elif text == "حساب کاربری 👤":
                await self.account_command(msg)

            elif text == "آپلود فایل 📥":
                m: Message = await msg.chat.ask("فایل مورد نظر خود را وارد نمایید:")
                if m.document:
                    downloading_msg: Message = await self.send_message(msg.chat.id, "در حال دانلود...")
                    print(await m.download((f := f"downloads/{msg.from_user.id}/{m.document.file_name}")))
                    filename = m.document.file_name
                    filesize = await human_readable(m.document.file_size)
                    url = "http://127.0.0.1:8000/get_from_europe"  # TODO: WILL CHANGE
                    user_id = str(msg.from_user.id)
                    async with ClientSession() as c:
                        await c.post(url, data={"user_id": user_id, "file": filename})
                    Links.create(
                        user_id=user_id,
                        filename=filename,
                        filesize=filesize,
                        file_link=(f_link := f"http://127.0.0.1:8000/download/{cipher.encrypt(f.encode()).decode()}"),
                        link_lifetime=datetime.now() + timedelta(seconds=10)
                    )

                    link_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("دانلود فایل 📤", url=f_link)]
                    ])
                    await downloading_msg.edit_text("نام فایل: {}\nحجم فایل: {}".format(filename, filesize))
                    await downloading_msg.edit_reply_markup(link_keyboard)

                else:
                    await self.send_message(msg.chat.id, "لطفا یک فایل ارسال کنید")
            elif text == "لینک های تولید شده 📎":
                username = (await self.get_me()).username
                if Links.get_or_none(user_id=msg.from_user.id):
                    final_text = "📥فایل های آپلود شده:\n"
                    for i, link in enumerate(Links.select().where(Links.user_id == str(msg.from_user.id)), start=1):
                        ti = str(link.link_lifetime - datetime.now())
                        if len(ti.split('.', 1)) > 1:
                            ti = ti.split('.', 1)[0]
                        t = await show_time(datetime.strptime(ti, "%H:%M:%S"))
                        final_text += f'''\n{i}- <a href="{link.file_link}">{link.filename}</a>
📦حجم فایل: {link.filesize}
⏳عمر لینک: {t}\n'''
                    final_text += f"\n@{username}"
                    await self.send_message(msg.chat.id, final_text, parse_mode=ParseMode.HTML)
                else:
                    await self.send_message(msg.chat.id, "شما لینکی تولید نکرده اید!❌")

        self.run()

    async def start_command(self, msg: Message):
        await self.send_message(msg.chat.id, "سلام بینیم", reply_markup=start_keyboard)
        if not User.get_or_none(user_id=msg.from_user.id):
            User.create(user_id=msg.from_user.id)

    async def account_command(self, msg):
        username = (await self.get_me()).username
        user = User.get(user_id=msg.from_user.id)
        traffic = user.traffic
        coin = user.coin
        members = user.members
        account_type = user.account_type
        download_files = user.download_files
        generated_links = user.generated_links
        file_limit_size = user.file_limit_size
        #  🛒🔑📥📤📦📊📎
        text = """
📊وضعیت حساب کاربری شما:

🎖نوع حساب شما: {}
🪙تعداد سکه های شما: {}
👥تعداد زیرمجموعه های شما: {}

📦ترافیک باقی مانده ی شما: {}
📁سقف حجم آپلود برای هر فایل: {}
📥تعداد فایل های دانلود شده: {}
📎تعداد لینک های تولید شده: {}
@{}""".format(account_type, coin, members, f"{traffic} مگابایت", f"{file_limit_size} مگابایت", download_files,
              generated_links, username)
        await self.send_message(msg.chat.id, text)


if __name__ == '__main__':
    Bot()
