import configparser
import os


def _get(name, config_file_data, default=None):
    val = os.environ.get(name,
                         config_file_data.get(name,
                                              default))
    if isinstance(default, bool) and not isinstance(val, bool):
        val = val.lower() in ("yes", "true", "y", "1")
    if default is None and val is None:
        raise EnvironmentError('Required parameter {} is not specified'.format(name))
    return val


try:
    config = configparser.ConfigParser()
    config.read('bot.ini')
    common = config['Common']
except (IOError, KeyError):
    common = {}

TOKEN = _get('TOKEN', common)
DATABASE_URL = _get('DATABASE_URL', common)
USE_WEBHOOK = _get('USE_WEBHOOK', common, True)
if USE_WEBHOOK:
    WEBHOOK_PORT = int(_get('PORT', common, '5000'))
    WEBHOOK_URL = _get('WEBHOOK_URL', common)

IMAGE_BLUR = _get('IMAGE_BLUR', common, True)
