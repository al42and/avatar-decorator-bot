#!/usr/bin/env python3

import logging
import io

import config
import graphics
from db import Color, initialize_database
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode, TelegramError
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler


def _generate_keyboard():
    colors_iter = Color.select()
    keyboard = [
            [InlineKeyboardButton(color.name, callback_data=color.name) for color in colors_iter]
            +
            [InlineKeyboardButton('Обновить', callback_data='__refresh')]
            ]
    return InlineKeyboardMarkup(keyboard)


def _refresh_keyboard(query):
    reply_markup = _generate_keyboard()
    try:
        query.edit_message_reply_markup(reply_markup=reply_markup)
    except TelegramError as e:
        if e.message == 'Message is not modified':
            # Okay, it happens
            pass
        else:
            raise


def _send_keyboard(update):
    reply_markup = _generate_keyboard()
    update.message.reply_text('Выберите экипаж:', reply_markup=reply_markup)


def _get_user_avatar(bot, user):
    avatars = user.get_profile_photos(limit=1)
    if avatars.total_count == 0:
        return None
    else:
        biggest_avatar = avatars.photos[0][-1]
        avatar_id = biggest_avatar.file_id
        fd = io.BytesIO()
        bot.get_file(avatar_id).download(out=fd)
        fd.seek(0)
        return fd


def _send_updated_avatar(bot, update, color):
    rgb = (color.r, color.g, color.b)
    user = update.effective_user
    chat_id = update.effective_chat.id
    avatar_fd = _get_user_avatar(bot, user)
    if avatar_fd:
        logging.info('Got avatar from %s; processing', user.name)
        image = graphics.add_color_to_avatar(avatar_fd, rgb)
    else:
        logging.info('Generating new avatar for %s', user.name)
        image = graphics.create_empty_avatar(rgb)
    logging.info('Sending updated avatar to chat %s', user.name)
    bot.send_photo(photo=image, chat_id=chat_id)


def start(bot, update):
    update.message.reply_text('Привет! Этот бот добавляет цветные кружки к аватаркам.')
    update.message.reply_text('Кружки́, а не кру́жки!')
    _send_keyboard(update)


def button(bot, update):
    query = update.callback_query
    if query.data == '__refresh':
        _refresh_keyboard(query)
        query.answer()
    else:
        try:
            color = Color.get(Color.name == query.data)
        except Color.DoesNotExist:
            _refresh_keyboard(query)
        else:
            _send_updated_avatar(bot, update, color)
        finally:
            query.answer()


def set_color(bot, update, args):
    logging.info('Setting color (by %s): %s', update.effective_user.name, ' '.join(args))
    try:
        name = args[0]
        rgb = graphics.get_color(args[1:])
        try:
            color = Color.get(name=name)
        except Color.DoesNotExist:
            color = Color.create(name=name, r=0, g=0, b=0)
        color.r, color.g, color.b = rgb
        color.save()
    except (IndexError, ValueError):
        update.message.reply_text('Использование: /set _экипаж_ _цвет_', parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text('Готово!')
    _send_keyboard(update)


def rm_color(bot, update, args):
    logging.info('Removing color (by %s): %s', update.effective_user.name, ' '.join(args))
    try:
        name = args[0]
        color = Color.get(name=name)
        color.delete()
    except (IndexError, ValueError):
        update.message.reply_text('Использование: /rm _экипаж_', parse_mode=ParseMode.MARKDOWN)
    except Color.DoesNotExist:
        update.message.reply_text('Не могу найти такой экипаж')
    else:
        update.message.reply_text('Готово!')
    _send_keyboard(update)


def help(bot, update, **kwargs):
    update.message.reply_text(
        """Выберите свой экипаж, и бот сгенерирует тебе новую аватарку с цветной окантовкой!
        Добавить/поменять окрас: /set _экипаж_ _цвет_.
        Удалить окрас: /rm _экипаж_.
        Цвет можно задавать английскими словами, `#rrggbb` или м.б. ещё как.""", parse_mode=ParseMode.MARKDOWN)


def error(bot, update, error, **kwargs):
    logging.warning('Update "%s" caused error "%s"' % (update, error))


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    initialize_database()

    updater = Updater(config.TOKEN)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('set', set_color, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('rm', rm_color, pass_args=True))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling(poll_interval=5)
    #updater.start_webhook(listen='127.0.0.1', port=9001)
    updater.idle()
