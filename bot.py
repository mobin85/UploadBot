from pyrogram.types.messages_and_media.message import Message
from pyrogram import Client, filters
import pyromod.listen
from setting import *
from keyboard import *
from db import User


class Bot(Client):
    def __init__(self):
        super().__init__("bot", API_ID, API_HASH, bot_token=TOKEN)

        @self.on_message(filters=filters.private & filters.text)
        async def echo(_, msg: Message):
            text = msg.text
            chat = msg.chat.id
            if text == "/start":
                await self.start_command(msg)

            elif text == "حساب کاربری 👤":
                await self.account_command(msg)

            elif text == "آپلود فایل 📥":
                m: Message = msg.chat.ask("فایل مورد نظر خود را وارد نمایید:")
                await self.send_message(msg.chat.id, "نام فایل {}\nحجم فایل {}".format(m.document.file_name,
                                                                                       m.document.file_size))

        self.run()

    async def start_command(self, msg: Message):
        await self.send_message(msg.chat.id, "سلام بینیم", reply_markup=start_keyboard)
        if not User.get_or_none(user_id=msg.from_user.id):
            User.create(user_id=msg.from_user.id)

    async def account_command(self, msg):
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
            """.format(account_type, coin, members, f"{traffic} مگابایت", f"{file_limit_size} مگابایت", download_files,
                       generated_links)
        await self.send_message(msg.chat.id, text)


if __name__ == '__main__':
    Bot()
