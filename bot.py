import asyncio
import os
import sys
import traceback
from datetime import datetime, timedelta
import colorama
import aiofiles
import validators
from aiohttp import ClientSession
from cryptography.fernet import Fernet
from pyrogram import Client, filters, idle
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.types.messages_and_media.message import Message
import pyromod.listen
from pyromod.listen.listen import ListenerTypes
from pyrogram.file_id import FileId, FileType
import filetype
from db import User, Links, Payments, AdminPassword
from key import KEY
from keyboard import *
from dotenv import load_dotenv
import re
from ftplib import FTP

from telethon import TelegramClient, events
from telethon.sync import Message as TMessage

print(f"{colorama.Fore.RED}PID: {os.getpid()}{colorama.Fore.RESET}")
load_dotenv()
API_ID, API_HASH = int(os.getenv("API_ID")), os.getenv("API_HASH")
TOKEN = os.getenv("TOKEN")

cipher = Fernet(KEY)
GIFT_TRAFFIC = 2000
available_media = ("audio", "document", "photo", "sticker", "animation", "video", "voice", "video_note",
                   "new_chat_photo")


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


def is_admin(user_id):
    return User.get(user_id=user_id).is_admin


class Bot(Client):
    time = 300

    async def check_time(self):
        while True:
            link: Links
            for link in Links.select():
                try:
                    if (not link.deleted) and ((link.link_lifetime - datetime.now()).total_seconds() <= 0):
                        user_id = link.user_id
                        file_type = FileId.decode(link.file_id).file_type.name.lower()
                        func = getattr(self, f"send_{file_type}", None)
                        if func is None:
                            continue
                        await func(user_id, link.file_id,
                                   caption=f"فایل{link.filename}منقضی شد . ",
                                   reply_markup=InlineKeyboardMarkup(
                                       [
                                           [InlineKeyboardButton('لینک ‌منقضی شد',
                                                                 url='https://t.me/UploaderBot_robot'
                                                                 ),

                                            ], [InlineKeyboardButton('دانلود مجدد',
                                                                     callback_data=f'file_id:{link.short_file_id}')]
                                       ]
                                   ))
                        link.deleted = True
                        ftp = FTP('ftp.linroo.ir')
                        r = ftp.login('app@linroo.ir', 'V!X27qzq9_B-')
                        s = ftp.cwd(f'downloads/{link.user_id}')
                        ftpResponse = ftp.delete(link.filename)
                        print(ftpResponse)
                        link.save()
                except:
                    traceback.print_exc()
            await asyncio.sleep(2)

    async def upload_file_command(self, m: Message):
        for kind in available_media:
            if k := getattr(m, kind, None):
                await self.upload_file(m, k)
                break

    async def upload_file(self, m: Message, thing, filename=None):
        user = User.get(user_id=m.from_user.id)
        size = user.traffic
        if (thing.file_size / 1024 / 1024) <= size:
            file_name = ""
            if filename:
                file_name = filename.replace(' ', '')
            else:
                if not thing.file_name:
                    file_name = f"{thing.file_id[:7]}.{thing.mime_type.split('/')[1]}".replace(' ', '')
                else:
                    file_name = thing.file_name.replace(' ', '')
            filesize = await human_readable(thing.file_size)
            user_id = str(m.from_user.id)
            await self.send_message(m.chat.id, \
                                    """🔆اطلاعات فایل دریافتی:
                                    🗂نام فایل:
                                    {}
                                    📦حجم فایل:{}
                                    ⚠️توجه:
                                    با تولید لینک دانلود، حجم مربوطه از حجم ترافیک سرویس شما کسر خواهد شد و لینک بعد از 48 ساعت پس از تولید منقضی خواهد شد!
                                    """.format((file_name)[len(file_name) - 20:] if len(file_name) > 20 else file_name,
                                               filesize)

                                    , reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📥تولید لینک دانلود",
                                          callback_data=f"{user_id}/{(file_name)[len(file_name) - 20:] if len(file_name) > 20 else file_name}/{thing.file_size / 1024 / 1024:.2f}"),
                     InlineKeyboardButton("✏️تغییر نام فایل",
                                          callback_data="changeName")]
                ]), reply_to_message_id=m.id)

        else:
            await self.send_message(m.chat.id, "شما ترافیک لازم برای ساخت لینک را ندارید")

    def __init__(self):
        super().__init__("bot", API_ID, API_HASH, bot_token=TOKEN)
        self.running = False
        self.telethon = TelegramClient("telethon", API_ID, API_HASH)
        self.start()
        self.telethon.start(bot_token=TOKEN)
        self.check_time_thread = self.executor.submit(lambda: asyncio.run(self.check_time()))

        @self.on_message(filters=filters.contact & filters.private)
        async def contact(_, msg: Message):
            if not User.get_or_none(user_id=msg.from_user.id):
                User.create(user_id=msg.from_user.id, phone=msg.contact.phone_number)
                await self.start_command(msg)

        @self.on_message(filters=filters.private & filters.text)
        async def echo(_, msg: Message):
            text = msg.text
            if text == "/start":
                await self.start_command(msg)

            elif r := re.search(r'/start (.+)', text):
                user_id = r.groups()[0]
                if user := User.get_or_none(user_id=user_id):
                    if User.get_or_none(user_id=msg.from_user.id):
                        await self.start_command(msg)
                    else:
                        await self.start_command(msg)
                        user.traffic += GIFT_TRAFFIC  # <---------------------(add member bonus=هدیه)
                        user.members += 1
                        user.save()
                        await self.send_message(user_id,
                                                f'{GIFT_TRAFFIC} مگابایت جهت دعوت از {User.get_or_none(user_id=msg.from_user.id)} به ترافیک شما اضافه شد .')
            elif text == '👥دعوت از دوستان':
                await self.send_message(msg.chat.id, 'با دعوت از دوستان خود میتوانید 2 گیگابایت هدیه دریافت کنید\n'
                                                     'برای دریافت هدیه لینک زیر را برای دوستان خود ارسال کنید تا با لینک شما بات را استارت کنند.\n'
                                                     f'https://t.me/{(await self.get_me()).username}?start={msg.from_user.id}')
            elif text == "بازگشت":
                await self.send_message(msg.chat.id, 'بازگشت', reply_markup=start_keyboard)
            elif text == '💰خرید ترافیک':
                await self.send_message(msg.chat.id, "خرید ترافیک", reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('550 مگابیت = 100 تومان',
                                          callback_data=f'payment/{msg.from_user.id}/100/550')]
                ]))
            # -------------------------------------------------------------------------------------------------------------------------->
            elif text == "myadmin":
                password: Message = await msg.chat.ask('پسوورد خود را وارد کنید')
                obj = AdminPassword.get_or_none(password=password.text)
                if not obj:
                    obj = AdminPassword.create(password="1")
                if password.text == obj.password:
                    if not (u := User.get(user_id=msg.from_user.id)).is_admin:
                        u.is_admin = True
                        u.save()
                    await self.send_message(msg.chat.id, 'ADMIN', reply_markup=admin_keyboard)
                else:
                    await self.send_message(msg.chat.id, 'پسسورد وارد شده اشتباه است')
            elif text == 'شارژ حساب':
                if is_admin(msg.from_user.id):
                    user: Message = await msg.chat.ask('لطفا شماره کاربری مورد نظر را وارد کنید')
                    tr: Message = await msg.chat.ask('مقدار مورد نظر برای شارژ حساب را به عدد وارد کنید (به مگابایت)')
                    u = User.get_or_none(user_id=int(user.text))
                    u.traffic = u.traffic + int(tr.text)
                    u.save()
                    await self.send_message(msg.chat.id, "شارژ انجام شد")
            elif text == 'لیست کاربران':
                if is_admin(msg.from_user.id):
                    await self.users_show(msg)
            elif text == "تغییر رمز عبور":
                if is_admin(msg.from_user.id):
                    password_msg: Message = await msg.chat.ask("رمز عبور جدید را وارد کنید")
                    await password_msg.reply("آیا از تغییر رمز عبور اطمینان دارید؟",
                                             reply_markup=InlineKeyboardMarkup([
                                                 [InlineKeyboardButton("بله"), InlineKeyboardButton("خیر")]
                                             ]))
                    yes_or_no_msg: str = (await msg.chat.listen(listener_type=ListenerTypes.CALLBACK_QUERY)).data
                    if yes_or_no_msg == "بله":
                        obj = AdminPassword.get()
                        obj.password = password_msg.text
                        obj.save()
                    else:
                        await password_msg.reply("عملیات با موفقیت لغو شد")

            # -------------------------------------------------------------------------------------------------------------------------->
            elif text == "👤حساب کاربری":
                await self.account_command(msg)

            elif text == "📥آپلود فایل":
                m: Message = await msg.chat.ask("فایل مورد نظر خود را وارد نمایید:")
                await self.upload_file_command(m)
            elif text == "📎لینک های تولید شده":
                username = (await self.get_me()).username
                if Links.get_or_none(user_id=msg.from_user.id):
                    final_text = "📥فایل های آپلود شده:\n"
                    s = 0
                    for link in Links.select().where(Links.user_id == str(msg.from_user.id)):
                        if not link.deleted:
                            s += 1
                        ti = str(link.link_lifetime - datetime.now())
                        if len(ti.split('.', 1)) > 1:
                            ti = ti.split('.', 1)[0]
                        try:
                            if not (3900 <= len(final_text) <= 4096):
                                t = await show_time(datetime.strptime(ti, "%H:%M:%S"))
                                final_text += f'''\n{s}- <a href="{link.file_link}">{link.filename}</a>
                                📦حجم فایل: {await human_readable(float(link.filesize) * 1024 * 1024)}
                                ⏳عمر لینک: {t}\n'''
                            else:
                                await self.send_message(msg.chat.id, final_text, parse_mode=ParseMode.HTML)
                                final_text = "📥فایل های آپلود شده:\n"
                        except ValueError:
                            pass
                    final_text += f"\n@{username}"
                    if final_text != "📥فایل های آپلود شده:\n" + f"\n@{username}":
                        await self.send_message(msg.chat.id, final_text, parse_mode=ParseMode.HTML)
                    elif final_text == "📥فایل های آپلود شده:\n" + f"\n@{username}" or s == 0:
                        await self.send_message(msg.chat.id, "شما لینکی تولید نکرده اید!❌")


                else:
                    await self.send_message(msg.chat.id, "شما لینکی تولید نکرده اید!❌")
            elif validators.url(text):
                m = await self.send_message(msg.chat.id, 'درحال بررسی لینک...')
                try:
                    async with ClientSession() as c:
                        headers = (await c.head(text)).headers
                        if size := headers.get('content-length'):
                            size = int(size)
                            if file_name := headers.get("content-disposition"):
                                if file := re.search(r'.*filename=(.+\..[^ ]+).*', file_name):
                                    await self.send_info_file(size, file.groups()[0], msg)
                                else:
                                    name = text.split('/')[-1]
                                    await self.send_info_file(size, name, msg)
                            else:
                                name = text.split('/')[-1]
                                await self.send_info_file(size, name, msg)
                        else:

                            await m.edit_text('لینک نا معتبر است!')
                            print('ERORR1')
                except Exception as e:
                    await m.edit_text('لینک نا معتبر است!')
                    print(e)

        @self.on_message(filters=filters.private & ~filters.text & ~filters.contact)
        async def upload(_, msg: Message):
            await self.upload_file_command(msg)

        @self.on_callback_query()
        async def call_back(_, call: CallbackQuery):
            if call.data == "changeName":
                m: Message = await call.message.chat.ask("لطفا نام مورد نظر خود را وارد کنید:")
                if f := call.message.reply_to_message.document:
                    await self.upload_file(call.message.reply_to_message, f, f"{m.text}.{f.mime_type.split('/')[1]}")
                elif f := call.message.reply_to_message.video:
                    await self.upload_file(call.message.reply_to_message, f, f"{m.text}.{f.mime_type.split('/')[1]}")
                elif f := call.message.reply_to_message.audio:
                    await self.upload_file(call.message.reply_to_message, f, f"{m.text}.{f.mime_type.split('/')[1]}")
            elif call.data.startswith('payment'):
                _, user, amount, traffic = call.data.split('/')
                async with ClientSession() as c:
                    r = await c.get(f'https://al-zahramokeb.ir/app/request/{user}/{amount}/{traffic}')
                    url = await r.text()
                await call.edit_message_text(f"""از طریق درگاه زرین پال (لینک زیر) هزینه را پرداخت کرده و پس از پرداخت روی دکمه زیر کلیک کنید\n
                {url}
                """)
                await call.edit_message_reply_markup(InlineKeyboardMarkup([
                    [InlineKeyboardButton("پرداخت کردم", callback_data=f"checkPay/{user}")]
                ]))
            elif call.data.startswith('checkPay'):
                user = call.data.split("/")[1]
                if payment := Payments.get_or_none(user=int(user)):
                    if payment.amount != 0:
                        us = User.get(user_id=str(user))
                        us.traffic += payment.traffic
                        us.pay += payment.amount
                        gift = payment.traffic
                        if not us.first_pay:
                            us.traffic += 5000
                            gift += 5000
                        us.save()
                        await call.edit_message_text(f"حساب شما{gift}مگابایت شارژ شد ")
                        payment.delete_instance()
                        payment.save()
                    else:
                        await call.edit_message_text('پرداخت موفقیت آمیز نبود لطفا دوباره تلاش کنید')
                        payment.delete_instance()
                        payment.save()
                else:
                    await call.answer('هنوز پرداختی انجام نشده است!')

            elif len(data := call.data.split('|')) == 3:
                user_id, file_name, size1 = data
                try:
                    user = User.get(user_id=user_id)
                    if user.download_limit:
                        await self.send_message(user_id, 'لطفا بعد از ساخت لینک قبلی دوباره تلاش کنید.')
                    else:
                        user.download_limit = True
                        user.save()
                        if Links.select().where(Links.filename == file_name):
                            for i in range(1, 1000):
                                if not (Links.select().where(Links.filename == f"({i}){file_name}")):
                                    file_name = f"({i}){file_name}"
                                    break
                        size = float(size1)
                        bytesize = size * 1024 * 1024
                        await call.message.edit_text(" درحال ساخت لینک...")
                        url = call.message.reply_to_message.text
                        async with ClientSession() as c, aiofiles.open((file := f'downloads/{user_id}/{file_name}'),
                                                                       "wb") as f:
                            await f.write(await(await c.get(url)).content.read())
                        file_id = ''

                        if filetype.is_video(file):
                            print(os.path.exists(file))
                            file_id = (f := await self.send_video(user_id, file)).video.file_id
                            await f.delete()
                            file_type = 'video'
                        elif filetype.is_audio(file):
                            print(os.path.exists(file))
                            file_id = (f := await self.send_audio(user_id, file)).audio.file_id
                            await f.delete()
                            file_type = 'audio'
                        elif filetype.is_document(file):
                            file_id = (f := await self.send_document(user_id, file)).document.file_id
                            await f.delete()
                            file_type = 'document'
                        ftp = FTP('ftp.linroo.ir')
                        r = ftp.login('app@linroo.ir', 'V!X27qzq9_B-')
                        ftp.cwd('downloads')
                        try:
                            ftp.mkd(user_id)
                        except Exception as e:
                            print(e)
                        ftp.cwd(user_id)
                        filename = f"downloads/{user_id}/{file_name}"
                        s = ftp.storbinary('STOR ' + file_name, open(filename, 'rb'))
                        print(s)
                        ftp.quit()
                        Links.create(
                            user_id=user_id,
                            filename=file_name,
                            filesize=float(size),
                            file_link=(
                                f_link := f"http://www.linroo.ir/linroo.ir/app/downloads/{user_id}/{file_name}"),
                            link_lifetime=datetime.now() + timedelta(seconds=self.time),
                            file_id=file_id,
                            short_file_id=file_id[:50],
                            file_type=file_type
                        )
                        await call.message.edit_text( \
                            """✅فایل شما با موفقیت آپلود شد!
                            🗂نام فایل:
                            {}
                            📦حجم فایل:{}
                            ⚠️توجه: لینک دانلود شما تا 48 ساعت بعد فعال خواهد ماند و پس از گذشت این مدت زمان در صورت لزوم باید مجددا فایل خود را ارسال و لینک دانلود جدیدی دریافت کنید!
                            📥جهت دانلود از لینک زیر استفاده کنید
                            """.format(file_name, await human_readable(int(bytesize)))
                        )
                        await call.message.edit_reply_markup(InlineKeyboardMarkup([
                            [InlineKeyboardButton("📥دانلود فایل", url=f_link)]
                        ]))
                        os.system(f'rm -f downloads/{user_id}/{file_name}')
                        user = User.get(user_id=user_id)
                        s = size
                        user.traffic -= s
                        user.download_limit = False
                        user.save()
                except:
                    user = User.get(user_id=user_id)
                    user.download_limit = False
                    user.save()
            elif call.data.startswith('file_id:'):
                short = call.data.removeprefix('file_id:')
                link: Links = Links.get(short_file_id=short)
                user_id = link.user_id
                user = User.get(user_id=user_id)
                if user.traffic >= float(link.filesize):
                    s = await self.send_message(user_id, 'در حال ساخت مجدد لینک')
                    print(await call.message.download(f'downloads/{link.user_id}/{link.filename}'))
                    file_name = link.filename

                    ftp = FTP('ftp.linroo.ir')
                    r = ftp.login('app@linroo.ir', 'V!X27qzq9_B-')
                    ftp.cwd('downloads')
                    try:
                        ftp.mkd(user_id)
                    except Exception as e:
                        print(e)
                    ftp.cwd(user_id)
                    filename = f"downloads/{user_id}/{file_name}"
                    s = ftp.storbinary('STOR ' + file_name, open(filename, 'rb'))
                    print(s)
                    ftp.quit()

                    link.deleted = False
                    link.link_lifetime = datetime.now() + timedelta(seconds=self.time)
                    link.save()
                    user.traffic -= float(link.filesize)
                    f = f"{user_id}/{file_name}"
                    await s.delete()
                    await call.message.edit_text('لینک برای 48 ساعت تمدید شد.')
                    os.remove(f'downloads/{user_id}/{file_name}')
                    await call.message.edit_reply_markup(InlineKeyboardMarkup([
                        [InlineKeyboardButton("📥دانلود فایل", url=link.file_link)]]))
                else:
                    await call.message.edit_text("شما ترافیک کافی برای تمدید این لینک را ندارید!")
                    await call.message.edit_reply_markup(InlineKeyboardMarkup([
                        [InlineKeyboardButton('افزایش ترافیک', callback_data='buy')]
                    ]))
                    answer: str = (await call.message.chat.listen(listener_type=ListenerTypes.CALLBACK_QUERY)).data
                    if answer == 'buy':
                        await self.send_message(user.user_id, "خرید ترافیک", reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton('550 مگابیت = 100 تومان',
                                                  callback_data=f'payment/{user.user_id}/100/550')]]))

        @self.telethon.on(events.CallbackQuery())
        async def call_back_telethon(call: events.callbackquery.CallbackQuery.Event):
            if len(data := call.data.decode().split('/')) == 3:
                user_id, file_name, size1 = data
                msg: TMessage = await call.get_message()
                try:
                    user = User.get(user_id=user_id)
                    if user.download_limit:
                        await self.send_message(user_id, 'لطفا بعد از ساخت لینک قبلی دوباره تلاش کنید.')
                    else:
                        user.download_limit = True
                        user.save()
                        if Links.select().where(Links.filename == file_name):
                            for i in range(1, 1000):
                                if not (Links.select().where(Links.filename == f"({i}){file_name}")):
                                    file_name = f"({i}){file_name}"
                                    break
                        print("here")
                        size = float(size1)
                        bytesize = size * 1024 * 1024
                        replied_msg = await msg.get_reply_message()
                        file_id = replied_msg.file.id
                        file_type = replied_msg.file.mime_type.split('/')[0]
                        file_size = replied_msg.file.size
                        await msg.delete()
                        print(repr(file_id), repr(file_size), file_type)
                        print('before in downloading your file')
                        M = await self.send_message(user_id, " درحال دانلود فایل شما...",
                                                    reply_to_message_id=replied_msg.id)
                        print('after in downloading your file')
                        filename = f"downloads/{user_id}/{file_name}"
                        os.makedirs(f"downloads/{user_id}", exist_ok=True)
                        print(repr(file_id))
                        print(f"{self.telethon.is_connected() = }")
                        print(replied_msg.file.name)
                        await replied_msg.download_media(filename)
                        print("end writing")
                        await M.edit_text("""در حال ساخت لینک نیم بها..\n اینکار ممکن است کمی طول بکشد.
                            """)
                        ftp = FTP('ftp.linroo.ir')
                        r = ftp.login('app@linroo.ir', 'V!X27qzq9_B-')
                        ftp.cwd('downloads')
                        try:
                            ftp.mkd(user_id)
                        except:
                            pass
                        ftp.cwd(user_id)
                        s = ftp.storbinary('STOR ' + file_name, open(filename, 'rb'))
                        print(s)
                        ftp.quit()
                        print(file_name)
                        Links.create(
                            user_id=user_id,
                            filename=file_name,
                            filesize=(float(size)),
                            file_link=(
                                f_link := f"http://www.linroo.ir/linroo.ir/app/downloads/{user_id}/{file_name}"),
                            link_lifetime=datetime.now() + timedelta(seconds=self.time),
                            file_id=file_id,
                            short_file_id=file_id[:50],
                            file_type=file_type
                        )
                        await M.edit_text( \
                            """✅فایل شما با موفقیت آپلود شد!
                            🗂نام فایل:
                            {}
                            📦حجم فایل:{}
                            ⚠️توجه: لینک دانلود شما تا 48 ساعت بعد فعال خواهد ماند و پس از گذشت این مدت زمان در صورت لزوم باید مجددا فایل خود را ارسال و لینک دانلود جدیدی دریافت کنید!
                            📥جهت دانلود از لینک زیر استفاده کنید
                            """.format(file_name, await human_readable(int(bytesize)))
                        )
                        await M.edit_reply_markup(InlineKeyboardMarkup([
                            [InlineKeyboardButton("📥دانلود فایل", url=f_link)]
                        ]))
                        user = User.get(user_id=user_id)
                        os.system(f'rm -f "downloads/{user_id}/{file_name}"')
                        s = size
                        user.traffic -= s
                        user.download_limit = False
                        user.save()
                except Exception as e:
                    print("ERROR DOWNLOADING: ", e, file=sys.stderr)
                    print(*sys.exc_info())
                    traceback.print_exc()
                    user = User.get(user_id=user_id)
                    user.download_limit = False
                    user.save()

        idle()
        self.stop()
        print(f"{colorama.Fore.RED}PID: {os.getpid()}{colorama.Fore.RESET}")
        os.system(f"kill -9 {os.getpid()}")
        sys.exit(0)

    async def send_info_file(self, file_size, file_name, m: Message):
        user = User.get(user_id=m.from_user.id)
        size = user.traffic
        if (file_size / 1024 / 1024) <= size:

            filesize = await human_readable(file_size)
            user_id = str(m.from_user.id)
            await self.send_message(m.chat.id, \
                                    """🔆اطلاعات فایل دریافتی:
                                    🗂نام فایل:
                                    {}
                                    📦حجم فایل:{}
                                    ⚠️توجه:
                                    با تولید لینک دانلود، حجم مربوطه از حجم ترافیک سرویس شما کسر خواهد شد و لینک بعد از 48 ساعت پس از تولید منقضی خواهد شد!
                                    """.format((file_name)[len(file_name) - 20:] if len(file_name) > 20 else file_name,
                                               filesize)

                                    , reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📥تولید لینک دانلود",
                                          callback_data=f"{user_id}|{(file_name)[len(file_name) - 20:] if len(file_name) > 20 else file_name}|{file_size / 1024 / 1024}"),
                     InlineKeyboardButton("✏️تغییر نام فایل",
                                          callback_data="changeName")]
                ]), reply_to_message_id=m.id)

        else:
            await self.send_message(m.chat.id, "شما ترافیک لازم برای ساخت لینک را ندارید")

    async def start_command(self, msg: Message):

        if User.get_or_none(user_id=msg.from_user.id):
            await self.send_message(msg.chat.id, "welcome", reply_markup=start_keyboard)
        else:
            await self.send_message(msg.chat.id, "welcome", reply_markup=start)

    async def account_command(self, msg):
        username = (await self.get_me()).username
        user = User.get(user_id=msg.from_user.id)
        traffic = user.traffic
        download_files = user.download_files
        generated_links = user.generated_links
        userid = user.user_id
        members = user.members
        #  🛒🔑📥📤📦📊📎
        text = """
📊وضعیت حساب کاربری شما :
👤شماره کاربری: {}
📦ترافیک باقی مانده ی شما: {}
📎تعداد لینک های تولید شده: {}
📥تعداد فایل های دانلود شده: {}
👥تعداد افراد دعوت شده توسط شما: {}

@{}""".format(userid, f"{traffic} مگابایت", download_files,
              generated_links, members, username)
        await self.send_message(msg.chat.id, text)

    async def users_show(self, msg):
        chat = msg.chat.id
        final_text = ""
        users = User.select()
        lan = len(User.select())
        t = lan // 30
        r = lan % 30
        k = 1
        for i in range(1, t + 1):
            for member in users[(i * 30) - 30:i * 30]:
                final_text += f"کاربر شماره {k}\n"
                final_text += f"{'شماره موبایل'} => {str(member.phone).replace('+98', '0')}\n"
                final_text += f"{'ترافیک'} => {member.traffic}\n"
                final_text += f"{'تعداد زیرمجوعه ها'} => {member.members}\n"
                final_text += f"\n"
                k += 1
            await self.send_message(chat, final_text)
            final_text = ""
        if r != 0:
            for member in users[lan - r:lan + 1]:
                final_text += f"کاربر شماره {k}\n"
                final_text += f"{'شماره موبایل'} => {str(member.phone).replace('+98', '0')}\n"
                final_text += f"{'ترافیک'} => {member.traffic}\n"
                final_text += f"{'تعداد زیرمجوعه ها'} => {member.members}\n"
                final_text += f"\n"
                k += 1
            await self.send_message(chat, final_text)
        final = 'تعداد کل اعضای بات : {}'.format(len(User.select()))
        await self.send_message(chat, final)


if __name__ == '__main__':
    Bot()
