#!/usr/bin/env python3

import logging
import io

import config
import graphics
import db
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


REFRESH_KEYWORD = '⟳'


def _generate_keyboard():
    colors_iter = db.Color.select()
    buttons = [KeyboardButton(color.name) for color in colors_iter] + [KeyboardButton(REFRESH_KEYWORD)]
    keyboard = list(zip(buttons[0::2], buttons[1::2]))
    if len(buttons) % 2 == 1:
        # zip stops when at least one iterator is exhausted. So, we need to handle odd number of values specially.
        keyboard.append([buttons[-1]])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def _refresh_keyboard(update):
    _send_keyboard(update)


def _send_keyboard(update):
    reply_markup = _generate_keyboard()
    update.message.reply_text('Выберите экипаж:', reply_markup=reply_markup)


def _get_user_avatar(bot, user):
    avatars = user.get_profile_photos(limit=1)
    if avatars.total_count == 0:
        return None
    else:
        biggest_avatar = avatars.photos[0][-1]
        return _get_image_from_photo(bot, biggest_avatar)


def _get_image_from_photo(bot, photo):
        avatar_id = photo.file_id
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
    logging.info('Sending updated avatar to %s', user.name)
    bot.send_photo(photo=image, chat_id=chat_id)


def _update_last_user_choice(user_id, color):
    try:
        lc = db.LastUserChoice.get(db.LastUserChoice.user_id == user_id)
        lc.color = color
        lc.save()
    except db.LastUserChoice.DoesNotExist:
        db.LastUserChoice.create(user_id=user_id, color=color)


def handler_start(bot, update):
    logging.info('%s started the bot', update.effective_user.name)
    update.message.reply_text('Привет! Этот бот добавляет цветные кружки к аватаркам.')
    update.message.reply_text('Кружки́, а не кру́жки!')
    _send_keyboard(update)


def handler_help(bot, update):
    update.message.reply_text(
        'Выбери свой экипаж, и бот сгенерирует тебе новую аватарку с цветной окантовкой!\n'
        'А ещё можно скидывать ему картинки, и он их раскрасит в цвета последнего выбранного экипажа.\n'
        'Добавить/поменять окрас: /set _экипаж_ _цвет_.\n'
        'Удалить окрас: /rm _экипаж_.\n'
        'Цвет можно задавать английскими словами, `#rrggbb` или м.б. ещё как.\n',
        parse_mode=ParseMode.MARKDOWN)


def handler_set(bot, update, args):
    logging.info('Setting color (by %s): %s', update.effective_user.name, ' '.join(args))
    try:
        name = args[0]
        rgb = graphics.get_color(args[1:])
        try:
            color = db.Color.get(name=name)
        except db.Color.DoesNotExist:
            color = db.Color.create(name=name, r=0, g=0, b=0)
        color.r, color.g, color.b = rgb
        color.save()
    except (IndexError, ValueError):
        update.message.reply_text('Использование: /set _экипаж_ _цвет_', parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text('Готово!')
    _send_keyboard(update)


def handler_rm(bot, update, args):
    logging.info('Removing color (by %s): %s', update.effective_user.name, ' '.join(args))
    try:
        name = args[0]
        color = db.Color.get(name=name)
        color.delete_instance()
    except (IndexError, ValueError):
        update.message.reply_text('Использование: /rm _экипаж_', parse_mode=ParseMode.MARKDOWN)
    except db.Color.DoesNotExist:
        update.message.reply_text('Не могу найти такой экипаж')
    else:
        update.message.reply_text('Готово!')
    _send_keyboard(update)


def handler_message(bot, update):
    data = update.message.text
    logging.info('Got <%s> from %s', data, update.effective_user.name)
    if data == 'REFRESH_KEYWORD':
        _refresh_keyboard(update)
    else:
        try:
            color = db.Color.get(db.Color.name == data)
        except db.Color.DoesNotExist:
            _refresh_keyboard(update)
        else:
            _send_updated_avatar(bot, update, color)
            _update_last_user_choice(update.effective_user.id, color)


def handler_photo(bot, update):
    photo = update.message.photo[-1]  # Last element is the biggest
    user = update.effective_user
    logging.info('Got photo from %s', user.name)
    try:
        color = db.LastUserChoice.get(db.LastUserChoice.user_id == user.id).color
    except db.LastUserChoice.DoesNotExist:
        update.message.reply_text('Сначала выбери экипаж, а потом пошли фотку! (Да, я при этом пришлю обработанную аватарку. Но мне не лень!)')
    except db.Color.DoesNotExist:
        update.message.reply_text('Выбери новый экипаж и пошли фотку снова!')
    else:
        rgb = (color.r, color.g, color.b)
        image = _get_image_from_photo(bot, photo)
        image = graphics.add_color_to_avatar(image, rgb)
        logging.info('Sending updated avatar to %s', user.name)
        bot.send_photo(photo=image, chat_id=update.effective_chat.id)


def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    db.initialize_database()

    updater = Updater(config.TOKEN)

    updater.dispatcher.add_handler(CommandHandler('start', handler_start))
    updater.dispatcher.add_handler(CommandHandler('help', handler_help))
    updater.dispatcher.add_handler(CommandHandler('set', handler_set, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('rm', handler_rm, pass_args=True))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handler_message))
    updater.dispatcher.add_handler(MessageHandler(Filters.photo, handler_photo))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling(poll_interval=5)
    #updater.start_webhook(listen='127.0.0.1', port=9001)
    updater.idle()
