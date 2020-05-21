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
                      InlineKeyboardMarkup, InlineKeyboardButton, Message)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

# Loading credentials.
with open('credentials.json') as json_file:
    data = json.load(json_file)
    TOKEN = data['TOKEN']
    REQUEST_KWARGS = data['REQUEST_KWARGS']

# Enable logging.
logging.basicConfig(format='%(asctime)s [%(name)s] [%(levelname)s]: %(message)s',
                    level=logging.INFO,
                    handlers=[
                        logging.FileHandler("info.log"),
                        logging.StreamHandler()])
logger = logging.getLogger(__name__)


# --- Message deletion handling methods ---

CHECK = range(1)

def delete(update, context):
    """Start post deletion.

    Ask user post ID.
    """

    update.message.reply_text(
        'Давай удалим пост.\n' 
        'Какой у него ID?\n\n'
        'Введи /cancel, чтобы отменить.')

    return CHECK

def check_del(update, context):
    """Deleting post.
    
    1) Load messages from file.
    2) Try to find message with given Id.
    3) Check if message author and user match.
    4) Delete message from file and channel.
    """

    user = update.message.from_user
    message_id = int(update.message.text)

    logger.info("(%s) intend to delete message (%s)", user.name, message_id)

    # Loading messages from file.
    with open('message_history.json') as json_file: 
        data = json.load(json_file) 
        messages = [eval(message) for message in data['messages']]

    point_message = {}

    # Searching in file for our message
    # (with same message_id).
    for message in messages:
        if message['message_id'] == message_id:
            point_message = message

    # Check if message with given id exists.
    if point_message == {}:
        logger.info("Hadn't found message to delete with Id (%s)", message_id)
        update.message.reply_text(
                'Не нашли сообщение с номером {}.'.format(message_id))

        help_bot(update, context)
        return ConversationHandler.END
    else:
        logger.info("Found message to delete with Id (%s)", message_id)

        # Check if message author and user match.
        message_user_id = point_message['entities'][-1]['user']['id']
        print(message_user_id)
        if (user.id != message_user_id):
            logger.info("User Id (%s) doesn't match "
                        "with message user Id (%s)",
                        user.id, message_user_id)
            update.message.reply_text(
                        'К сожалению, ты можешь удалить ' 
                        'только свой пост.')

            help_bot(update, context)
            return ConversationHandler.END
        else:
            logger.info("User Id (%s) match "
                        "with message user Id (%s)",
                        user.id, message_user_id)

            logger.info("(%s) deleting "
                        "message (%s)",
                        user.name, message_id)

            # Deleting message from chat.
            context.bot.delete_message(
                    chat_id='@matobes_news', 
                    message_id=message_id)

            # Deleting message from file.
            with open('message_history.json') as json_file: 
                data = json.load(json_file) 
                temp = data['messages'] 
            for msg in temp:
                if str(message_id) in msg:
                    temp.remove(msg)
            with open('message_history.json', 'w') as json_file: 
                json.dump(data, json_file, indent=4) 

            update.message.reply_text(
                    'Сообщение с номером {} удалено!'.format(message_id))

    help_bot(update, context)

    return ConversationHandler.END

def cancel_del(update, context):
    """Cancel conversation."""

    user = update.message.from_user

    logger.info("(%s) canceled the conversation", user.name)

    update.message.reply_text(
        'Отменяем удаление сообщения.\n\n',
        reply_markup=ReplyKeyboardRemove())

    help_bot(update, context)

    return ConversationHandler.END


# --- Message add handling methods ---

GROUP, SUBJECT, INFO, SEND = range(4)

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

    Ask user for message subject.
    """

    # Writing group that we got to buffer.
    context.user_data['group'] = update.message.text

    user = update.message.from_user
    logger.info("(%s) intend to send to (%s)", user.name, update.message.text)

    update.message.reply_text(
        'Хорошо.\n'
        'Добавь тему сообщения:',
        reply_markup=ReplyKeyboardRemove())

    return SUBJECT

def subject(update, context):
    """Receive message subject.

    Ask user for information he want to add.
    """
    context.user_data['subject'] = update.message.text

    user = update.message.from_user
    logger.info("(%s) intend to add subject (%s)", user.name, update.message.text)

    update.message.reply_text(
        'Теперь добавь информацию, '
        'которой хочешь поделиться\n'
        '(только текст):')

    return INFO

def info(update, context):
    """Receive content to send.

    Send formatted message to user to preview it.
    Ask if he want to continue.
    """
    reply_keyboard = [['Отправляем!', '/cancel']]

    context.user_data['info'] = update.message.text

    user = update.message.from_user
    logger.info("(%s) intend to send info (%s)", user.name, update.message.text)

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

    logger.info("(%s) approved message sending", user.name)

    # Sending message to channel.
    msg=context.bot.send_message(
        chat_id='@matobes_news', 
        text=form_msg(update, context),
        parse_mode=telegram.ParseMode.MARKDOWN)

    # Writing message to file. 
    with open('message_history.json') as json_file: 
        data = json.load(json_file) 
        data['last_message_id'] = msg.message_id
        temp = data['messages'] 
        temp.append(str(msg)) 
    with open('message_history.json', 'w') as json_file: 
        json.dump(data, json_file, indent=4) 

    update.message.reply_text(
        'Отправляю сообщение на канал.\n\n',
        reply_markup=ReplyKeyboardRemove())

    help_bot(update, context)

    return ConversationHandler.END

def cancel_add(update, context):
    """Cancel conversation."""

    user = update.message.from_user

    logger.info("(%s) canceled the conversation", user.name)

    update.message.reply_text(
        'Отменяем создание сообщения.\n\n',
        reply_markup=ReplyKeyboardRemove())

    help_bot(update, context)

    return ConversationHandler.END


# --- Support methods -- -

def start(update, context):
    """Send a message when the command /start is issued."""

    update.message.reply_text(
        'Привет!\n\n'
        'Здесь ты можешь создать информационное сообщение '
        'для новостного канала матобеса:\n\n' 
        'https://t.me/matobes_news\n\n'
        'Для начала введи /help.')

def help_bot(update, context):
    """Send a message when the command /help is issued."""

    update.message.reply_text(
        'Доступные команды:\n\n'
        'Чтобы создать новое сообщение, введи \n /add.\n'
        'Чтобы удалить сообщение, введи \n /delete.')

def form_msg(update, context):
    """Format message."""

    msg = ""
    user = update.message.from_user

    # Getting message id from messages file.
    with open('message_history.json') as json_file: 
        data = json.load(json_file) 
        message_id = data['last_message_id'] 

    msg += "*Кому:* {}".format(context.user_data['group'])
    msg += "\n\n"
    msg += "*Тема:* {}".format(context.user_data['subject'])
    msg += "\n\n"
    msg += "{}".format(context.user_data['info'])
    msg += "\n\n"
    msg += "*Id:* {}".format(message_id + 1)
    msg += "\n"
    msg += "*От кого:* {}".format(user.mention_markdown())

    return msg

def error(update, context):
    """Log Errors caused by Updates."""

    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add message add handler with the states GROUP, SUBJECT, INFO, SEND.
    msg_add_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add)],

        states={
            GROUP: [MessageHandler(Filters.regex('^(Весь поток|341|344)$'), group)],

            SUBJECT: [MessageHandler(Filters.text, subject)],

            INFO: [MessageHandler(Filters.text, info)],

            SEND: [MessageHandler(Filters.regex('^(Отправляем!)$'), send)]
        },

        fallbacks=[CommandHandler('cancel', cancel_add)]
    )

    # Add message add handler with the states GROUP, INFO, SEND.
    msg_del_handler = ConversationHandler(
        entry_points=[CommandHandler('delete', delete)],

        states={
            CHECK: [MessageHandler(Filters.regex('^([0-9]*)$'), check_del)],
        },

        fallbacks=[CommandHandler('cancel', cancel_del)]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_bot))
    dp.add_handler(msg_add_handler)
    dp.add_handler(msg_del_handler)

    # Log all errors.
    dp.add_error_handler(error)

    # Start the Bot.
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
