#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bot helps creating posts 
to https://t.me/matobes_news channel.
"""

import logging
import telegram
import json

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, 
                      InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

# Loading credentials.
with open('credentials.json') as json_file:
    data = json.load(json_file)
    TOKEN=data['TOKEN']
    REQUEST_KWARGS=data['REQUEST_KWARGS']

# Enable logging.
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Conversation handling methods ---

GROUP, INFO, SEND = range(3)

def add(update, context):
    """Start post creation.

    Ask user to choose whom to send message.
    """

    reply_keyboard = [['Весь поток'], 
                      ['341', '344']]

    update.message.reply_text(
        'Создадим новое сообщение.\n' 
        'Кому оно предназначено?\n\n'
        'В любой момент введи /cancel, чтобы отменить.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return GROUP

def group(update, context):
    """Receive info about whom to send.

    Ask user for information he want to add.
    """

    # Writing group that we got to buffer.
    context.user_data['group'] = update.message.text

    user = update.message.from_user
    logger.info("User %s want to send msg to: %s", user.name, update.message.text)

    update.message.reply_text(
        'Хорошо.\n'
        'Теперь добавь информацию, '
        'которой хочешь поделиться:',
        reply_markup=ReplyKeyboardRemove())

    return INFO

def info(update, context):
    """Receive content to send.

    Send formatted message to user to preview it.
    Ask if he want to continue.
    """
    reply_keyboard = [['Отправляем!', '/cancel']]

    context.user_data['info'] = update.message.text

    user = update.message.from_user
    logger.info("User %s want to send info: %s", user.name, update.message.text)

    update.message.reply_text(
        'Отлично!\n' 
        'Давай проверим твоё сообщение перед отправкой:')

    update.message.reply_text(
        form_msg(update, context),
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        parse_mode=telegram.ParseMode.MARKDOWN)
    
    return SEND

def send(update, context):
    """Send approved message to channel."""

    user = update.message.from_user

    logger.info("User %s approved message sending", user.name)

    # Sending message to channel.
    context.bot.send_message(
        chat_id='@matobes_news', 
        text=form_msg(update, context),
        parse_mode=telegram.ParseMode.MARKDOWN)

    update.message.reply_text(
        'Отправляю сообщение на канал.\n\n'
        'Чтобы отправить ещё сообщение, введи \n /add.',
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

def cancel(update, context):
    """Cancel conversation."""

    user = update.message.from_user

    logger.info("User %s canceled the conversation.", user.name)

    update.message.reply_text(
        'Отменяем создание сообщения.\n\n'
        'Чтобы создать новое сообщение, введи \n /add.',
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


# --- Support methods -- -

def start(update, context):
    """Send a message when the command /start is issued."""

    update.message.reply_text(
        'Привет!\n\n'
        'Здесь ты можешь создать информационное сообщение '
        'для новостного канала матобеса:\n\n' 
        'https://t.me/matobes_news\n\n'
        'Для начала введи /add.')

def form_msg(update, context):
    """Format message."""

    msg = ""
    user = update.message.from_user

    msg += "*Кому:* {}".format(context.user_data['group'])
    msg += "\n\n"
    msg += "*Что:* {}".format(context.user_data['info'])
    msg += "\n\n"
    msg += "*От кого:* {}".format(user.mention_markdown())

    return msg

def error(update, context):
    """Log Errors caused by Updates."""

    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():

    updater = Updater(TOKEN, request_kwargs=REQUEST_KWARGS, use_context=True)
    dp = updater.dispatcher

    # Add conversation handler with the states GROUP, INFO, SEND
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add)],

        states={
            GROUP: [MessageHandler(Filters.regex('^(Весь поток|341|344)$'), group)],

            INFO: [MessageHandler(Filters.text, info)],

            SEND: [MessageHandler(Filters.regex('^(Отправляем!)$'), send)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
