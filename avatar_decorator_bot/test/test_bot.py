import unittest
from unittest.mock import patch, Mock

with patch('avatar_decorator_bot.config.DATABASE_URL', ':memory:'):
    from avatar_decorator_bot import bot, db


class TestBot(unittest.TestCase):
    def setUp(self):
        db.initialize_database()
        self.bot = bot
        self.bot.get_file = Mock()
        self.bot.send_photo = Mock()
        self.update = Mock()

    def tearDown(self):
        db.database.close()

    def test_handler_start(self):
        bot.handler_start(self.bot, self.update)
        self.update.message.reply_text.assert_called()

    def test_handler_help(self):
        bot.handler_help(self.bot, self.update)
        self.update.message.reply_text.assert_called()

    def test_handler_set_empty(self):
        bot.handler_set(self.bot, self.update, [])
        self.assertEqual(db.Color.select().count(), 0)
        self.update.message.reply_text.assert_called()

    def test_handler_set_no_color(self):
        # Should fail, because no color was provided for new car
        bot.handler_set(self.bot, self.update, ['Bread'])
        self.assertEqual(db.Color.select().count(), 0)
        self.update.message.reply_text.assert_called()

    def test_handler_set_normal(self):
        bot.handler_set(self.bot, self.update, ['Bread', '#c68958'])
        self.update.message.reply_text.assert_any_call('Готово!')
        self.assertEqual(db.Color.select().count(), 1)
        c = db.Color.get(db.Color.name == 'Bread')
        self.assertTrue(c.active)
        self.assertEqual(c.r, 0xc6)
        self.assertEqual(c.g, 0x89)
        self.assertEqual(c.b, 0x58)

    def test_handler_rm_empty(self):
        bot.handler_rm(self.bot, self.update, [])
        self.update.message.reply_text.assert_called()

    def test_handler_rm_non_existent(self):
        bot.handler_rm(self.bot, self.update, ['Bread'])
        self.update.message.reply_text.assert_any_call('Не могу найти такой экипаж')

    def test_handler_set_rm(self):
        bot.handler_set(self.bot, self.update, ['Bread', '#c68958'])
        self.update.message.reply_text.assert_any_call('Готово!')
        self.update.reset_mock()

        bot.handler_rm(self.bot, self.update, ['Bread'])
        self.update.message.reply_text.assert_any_call('Готово!')
        c = db.Color.get(db.Color.name == 'Bread')
        self.assertFalse(c.active)

    def test_handler_set_rm_recall(self):
        bot.handler_set(self.bot, self.update, ['Bread', '#c68958'])
        self.update.message.reply_text.assert_any_call('Готово!')
        self.update.reset_mock()

        bot.handler_rm(self.bot, self.update, ['Bread'])
        self.update.message.reply_text.assert_any_call('Готово!')
        self.update.reset_mock()

        bot.handler_set(self.bot, self.update, ['Bread'])
        self.update.message.reply_text.assert_any_call('Готово!')
        c = db.Color.get(db.Color.name == 'Bread')
        self.assertTrue(c.active)
        self.assertEqual(c.r, 0xc6)
        self.assertEqual(c.g, 0x89)
        self.assertEqual(c.b, 0x58)


if __name__ == '__main__':
    unittest.main()
