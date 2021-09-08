import unittest
from unittest.mock import patch, Mock

with patch('avatar_decorator_bot.config.DATABASE_URL', ':memory:'):
    from avatar_decorator_bot import bot, db


class TestBot(unittest.TestCase):
    def setUp(self):
        db.initialize_database()
        self.update = Mock()
        self.context = Mock()
        self.context.bot = bot
        self.context.bot.get_file = Mock()
        self.context.bot.send_photo = Mock()

    def tearDown(self):
        db.database.close()

    def test_handler_start(self):
        bot.handler_start(self.update, self.context)
        self.update.message.reply_text.assert_called()

    def test_handler_help(self):
        bot.handler_help(self.update, self.context)
        self.update.message.reply_text.assert_called()

    def test_handler_set_empty(self):
        self.context.args = []
        bot.handler_set(self.update, self.context)
        self.assertEqual(db.Color.select().count(), 0)
        self.update.message.reply_text.assert_called()

    def test_handler_set_no_color(self):
        # Should fail, because no color was provided for new car
        self.context.args = ['Break']
        bot.handler_set(self.update, self.context)
        self.assertEqual(db.Color.select().count(), 0)
        self.update.message.reply_text.assert_called()

    def test_handler_set_normal(self):
        self.context.args = ['Bread', '#c68958']
        bot.handler_set(self.update, self.context)
        self.update.message.reply_text.assert_any_call('Готово!')
        self.assertEqual(db.Color.select().count(), 1)
        color = db.Color.get(db.Color.name == 'Bread')
        self.assertTrue(color.active)
        self.assertEqual(color.r, 0xc6)
        self.assertEqual(color.g, 0x89)
        self.assertEqual(color.b, 0x58)

    def test_handler_rm_empty(self):
        self.context.args = []
        bot.handler_rm(self.update, self.context)
        self.update.message.reply_text.assert_called()

    def test_handler_rm_non_existent(self):
        self.context.args = ['Bread']
        bot.handler_rm(self.update, self.context)
        self.update.message.reply_text.assert_any_call('Не могу найти такой экипаж')

    def test_handler_set_rm(self):
        self.context.args = ['Bread', '#c68958']
        bot.handler_set(self.update, self.context)
        self.update.message.reply_text.assert_any_call('Готово!')
        self.update.reset_mock()

        self.context.args = ['Bread']
        bot.handler_rm(self.update, self.context)
        self.update.message.reply_text.assert_any_call('Готово!')
        color = db.Color.get(db.Color.name == 'Bread')
        self.assertFalse(color.active)

    def test_handler_set_rm_recall(self):
        self.context.args = ['Bread', '#c68958']
        bot.handler_set(self.update, self.context)
        self.update.message.reply_text.assert_any_call('Готово!')
        self.update.reset_mock()

        self.context.args = ['Bread']
        bot.handler_rm(self.update, self.context)
        self.update.message.reply_text.assert_any_call('Готово!')
        self.update.reset_mock()

        self.context.args = ['Bread']
        bot.handler_set(self.update, self.context)
        self.update.message.reply_text.assert_any_call('Готово!')
        color = db.Color.get(db.Color.name == 'Bread')
        self.assertTrue(color.active)
        self.assertEqual(color.r, 0xc6)
        self.assertEqual(color.g, 0x89)
        self.assertEqual(color.b, 0x58)


if __name__ == '__main__':
    unittest.main()
