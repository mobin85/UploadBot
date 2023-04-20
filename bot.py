from pyrogram.types.messages_and_media.message import Message
from pyrogram import Client, filters
from setting import *


class Bot(Client):
    def __init__(self):
        super().__init__("bot", API_ID, API_HASH, bot_token=TOKEN)

        @self.on_message(filters=filters.private)
        async def echo(_, msg: Message):
            text = msg.text
            chat = msg.chat.id
            if text == "/start":
                await self.start_command(msg)
                # changed something
        self.run()

    async def start_command(self, msg: Message):
        await self.send_message(msg.chat.id, "سلام بینیم")


Bot()
