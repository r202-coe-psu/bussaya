# Database Section
MONGODB_DB = 'bussayadb'

APP_TITLE = 'Bussaya'

CACHE_TYPE = 'simple'
OAUTH2_CACHE_TYPE = 'simple'

COE_LECTURERS = []

LOGIN_PROVIDER = ['GOOGLE', 'ENGPSU']

# Deadline-reminder emails (see bussaya/notifications.py). Disabled by
# default so dev/test environments never send real mail; set MAIL_ENABLED
# = True and the SMTP settings below in an environment's .cfg to enable.
MAIL_ENABLED = False
MAIL_HOST = 'localhost'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
MAIL_SENDER = ''
MAIL_SENDER_NAME = 'Bussaya'

# Used to build links back into the app from reminder emails, e.g.
# 'https://bussaya.example.com'. Left blank, emails omit the link line.
SITE_BASE_URL = ''
