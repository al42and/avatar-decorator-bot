import logging
import io

from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram import ParseMode, Update
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters

from avatar_decorator_bot import config, graphics, db

REFRESH_KEYWORD = '⟳'


def _generate_keyboard():
    colors_iter = db.Color.select().where(db.Color.active == True)
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
        logging.info('Sending updated avatar to %s', user.name)
        bot.send_photo(photo=image, chat_id=chat_id)
    else:
        logging.info('Generating new avatar for %s', user.name)
        image = graphics.create_empty_avatar(rgb)
        logging.info('Sending updated avatar to %s', user.name)
        bot.send_photo(photo=image, chat_id=chat_id)
        update.message.reply_text('Не вижу твою аватарку. Может быть, стоит меня добавить в список видящих? '
                                  'Settings -> Privacy & Security -> Profile Photo -> Always allow. '
                                  'Или пришли мне картинкой фото, которое надо раскрасить. '
                                  'А пока держи цветной квадратик.')


def _update_last_user_choice(user_id, color):
    db.LastUserChoice.insert(user_id=user_id, color=color).on_conflict(
                conflict_target=[db.LastUserChoice.user_id],
                preserve=[db.LastUserChoice.color]
            ).execute()


def handler_start(update: Update, _context: CallbackContext):
    logging.info('%s started the bot', update.effective_user.name)
    update.message.reply_text('Привет! Этот бот добавляет цветные кружки к аватаркам.')
    update.message.reply_text('Кружки́, а не кру́жки!')
    _send_keyboard(update)


def handler_help(update: Update, _context: CallbackContext):
    update.message.reply_text(
        'Выбери свой экипаж, и бот сгенерирует тебе новую аватарку с цветной окантовкой!\n'
        'А ещё можно скидывать ему картинки, и он их раскрасит в цвета последнего выбранного экипажа.\n'
        'Добавить/поменять окрас: /set _экипаж_ _цвет_.\n'
        'Удалить окрас: /rm _экипаж_.\n'
        'Цвет можно задавать английскими словами, `#rrggbb` или м.б. ещё как.\n',
        parse_mode=ParseMode.MARKDOWN)


def handler_set(update: Update, context: CallbackContext):
    args = context.args
    logging.info('Setting color (by %s): %s', update.effective_user.name, ' '.join(args))
    try:
        name = args[0]
        if len(args) > 1:
            rgb = graphics.get_color(args[1:])
        else:
            rgb = None

        try:
            color = db.Color.get(name=name)
        except db.Color.DoesNotExist:
            if rgb is None:
                update.message.reply_text('Цвет можно пропустить для известных экипажей, но я такого не знаю.', parse_mode=ParseMode.MARKDOWN)
                _send_keyboard(update)
                return
            color = db.Color.create(name=name, r=0, g=0, b=0)

        if rgb is not None:
            color.r, color.g, color.b = rgb
        color.active = True
        color.save()
    except (IndexError, ValueError):
        update.message.reply_text('Использование: /set _экипаж_ _цвет_. Если экипаж уже играл на моей памяти, то можно цвет не указывать.', parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text('Готово!')
    _send_keyboard(update)


def handler_rm(update: Update, context: CallbackContext):
    args = context.args
    logging.info('Removing color (by %s): %s', update.effective_user.name, ' '.join(args))
    try:
        name = args[0]
        color = db.Color.get(name=name)
        color.active = False
        color.save()
    except (IndexError, ValueError):
        update.message.reply_text('Использование: /rm _экипаж_', parse_mode=ParseMode.MARKDOWN)
    except db.Color.DoesNotExist:
        update.message.reply_text('Не могу найти такой экипаж')
    else:
        update.message.reply_text('Готово!')
    _send_keyboard(update)


def handler_message(update: Update, context: CallbackContext):
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
            if not color.active:
                update.message.reply_text('Этот экипаж сейчас не играет. Но так и быть, держи картинку.')
            _send_updated_avatar(context.bot, update, color)
            _update_last_user_choice(update.effective_user.id, color)


def handler_photo(update: Update, context: CallbackContext):
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
        image = _get_image_from_photo(context.bot, photo)
        image = graphics.add_color_to_avatar(image, rgb)
        logging.info('Sending updated avatar to %s', user.name)
        if not color.active:
            update.message.reply_text('Этот экипаж сейчас не играет. Но так и быть, держи картинку.')
        context.bot.send_photo(photo=image, chat_id=update.effective_chat.id)


def error(update: Update, context: CallbackContext):
    logging.warning('Update "%s" caused error "%s"', update, context.error)


def main_loop():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    db.initialize_database()

    updater = Updater(config.TOKEN, use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', handler_start))
    updater.dispatcher.add_handler(CommandHandler('help', handler_help))
    updater.dispatcher.add_handler(CommandHandler('set', handler_set, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('rm', handler_rm, pass_args=True))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handler_message))
    updater.dispatcher.add_handler(MessageHandler(Filters.photo, handler_photo))
    updater.dispatcher.add_error_handler(error)

    if config.USE_WEBHOOK:
        webhook_url = config.WEBHOOK_URL + config.TOKEN
        updater.start_webhook(listen="0.0.0.0",
                              port=config.WEBHOOK_PORT,
                              url_path=config.TOKEN,
                              webhook_url=webhook_url)
    else:
        updater.start_polling(poll_interval=5)
    updater.idle()
