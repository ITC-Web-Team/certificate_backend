"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from dotenv import load_dotenv
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

# Load environment variables
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# Configure WhiteNoise
application = WhiteNoise(
    application,
    root=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'staticfiles'),
    prefix='static/'
)
