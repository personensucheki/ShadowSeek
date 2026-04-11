# Gunicorn config for ShadowSeek
bind = '0.0.0.0:10000'
workers = 4
timeout = 60
accesslog = '-'
errorlog = '-'
loglevel = 'info'
preload_app = True
