import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'CHANGEME'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

ADMINS = (
#    ('Chris Karr', 'chris@audacious-software.com'),
)

SAMPLE_DATA_SOURCE = ''

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/django/pdk_site/static'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/django/pdk_site/media'

SITE_URL = 'https://historian.audacious-software.com/'
PDK_DASHBOARD_ENABLED = True

INTERNAL_IPS = [
]

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME':'',
        'USER': '',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
    }
}

if 'TRAVIS' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE':   'django.contrib.gis.db.backends.postgis',
            'NAME':     'travisci',
            'USER':     'postgres',
            'PASSWORD': '',
            'HOST':     'localhost',
            'PORT':     '',
        }
    }
