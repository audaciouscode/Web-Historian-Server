"""
WSGI config for pdk_site project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

path = '/var/www/django/pdk_site'

if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "historian.settings")

try:
    application = get_wsgi_application()
except Exception:
    print 'handling WSGI exception'
    # Error loading applications
    traceback.print_exc()
