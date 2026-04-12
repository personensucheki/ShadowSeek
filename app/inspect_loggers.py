import logging
from logging.handlers import RotatingFileHandler

def inspect_loggers():
    root_logger = logging.getLogger()
    app_logger = logging.getLogger('app')
    tiktok_logger = logging.getLogger('tiktok_provider')
    info = {}
    info['root_logger_level'] = logging.getLevelName(root_logger.getEffectiveLevel())
    info['app_logger_level'] = logging.getLevelName(app_logger.getEffectiveLevel())
    info['tiktok_provider_effective_level'] = logging.getLevelName(tiktok_logger.getEffectiveLevel())
    info['root_handlers'] = [(type(h).__name__, getattr(h, 'level', None), getattr(h, 'baseFilename', None)) for h in root_logger.handlers]
    info['app_handlers'] = [(type(h).__name__, getattr(h, 'level', None), getattr(h, 'baseFilename', None)) for h in app_logger.handlers]
    info['tiktok_handlers'] = [(type(h).__name__, getattr(h, 'level', None), getattr(h, 'baseFilename', None)) for h in tiktok_logger.handlers]
    info['tiktok_propagate'] = tiktok_logger.propagate
    print(info)

if __name__ == '__main__':
    inspect_loggers()
