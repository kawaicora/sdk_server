import asyncio
import threading
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackContext
from app.settings import DefaultConfig
from threading import Thread
from typing import (
    Optional,
    Union,
)

from telegram._utils.defaultvalue import DEFAULT_NONE
from telegram._utils.types import (
    JSONDict,
    ODVInput,
    ReplyMarkup,
)
from collections.abc import Sequence
from telegram._message import Message


class TelegramBot(Thread):
    def __init__(self,chat_id=None):
        super(TelegramBot,self).__init__()
        self.bot = Bot(token=DefaultConfig.TELEGRAM_BOT_TOKEN)
        if chat_id == None:
            self.chat_id = DefaultConfig.TELEGRAM_BOT_CHAT_ID
        else:
            self.chat_id = chat_id
        self.app = Application.builder().token(token=DefaultConfig.TELEGRAM_BOT_TOKEN).build()
        self.app.add_handler(CommandHandler("get_chat_id", self.get_chat_id_from_msg))
        self.start()

    def set_chat_id(self,chat_id:int):
        self.chat_id = chat_id
    def get_chat_id(self):
        return self.chat_id
    def run(self):
        
        # Create and set the event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Run the polling inside the event loop
            loop.run_until_complete(self.app.run_polling())

        except Exception as e:
            # Catch the exception to prevent the event loop from shutting down unexpectedly
            print(f"Error while running bot: {e}")
        finally:
            loop.close()  # Explicitly close the loop after running
        

    async def get_chat_id_from_msg(self,update:Update,context:CallbackContext):
        chat_id = update.message.chat_id
        await update.message.reply_text(f"当前 Chat ID: {chat_id}")
    def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: ODVInput[str] = DEFAULT_NONE,
        entities: Optional[Sequence["MessageEntity"]] = None,
        disable_notification: ODVInput[bool] = DEFAULT_NONE,
        protect_content: ODVInput[bool] = DEFAULT_NONE,
        reply_markup: Optional[ReplyMarkup] = None,
        message_thread_id: Optional[int] = None,
        link_preview_options: ODVInput["LinkPreviewOptions"] = DEFAULT_NONE,
        reply_parameters: Optional["ReplyParameters"] = None,
        business_connection_id: Optional[str] = None,
        message_effect_id: Optional[str] = None,
        allow_paid_broadcast: Optional[bool] = None,
        *,
        allow_sending_without_reply: ODVInput[bool] = DEFAULT_NONE,
        reply_to_message_id: Optional[int] = None,
        disable_web_page_preview: Optional[bool] = None,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: Optional[JSONDict] = None,
    ) -> Message:
        msg = None
        try:
            msg = asyncio.run(self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                entities=entities,
                disable_notification=disable_notification,
                protect_content=protect_content,
                reply_markup=reply_markup,
                message_thread_id=message_thread_id,
                link_preview_options=link_preview_options,
                reply_parameters=reply_parameters,
                business_connection_id= business_connection_id,
                message_effect_id= message_effect_id,
                allow_paid_broadcast= allow_paid_broadcast,
                allow_sending_without_reply = allow_sending_without_reply,
                reply_to_message_id = reply_to_message_id,
                disable_web_page_preview= disable_web_page_preview,
                read_timeout= read_timeout,
                write_timeout= write_timeout,
                connect_timeout= connect_timeout,
                pool_timeout= pool_timeout,
                api_kwargs= api_kwargs                
            ))
        except Exception as e:
            pass
        return msg