"""
WSGI config for psycho_platform project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.conf import settings  # ¡IMPORTANTE: AÑADE ESTA IMPORTACIÓN!
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'psycho_platform.settings')

application = get_wsgi_application()
application = WhiteNoise(application, root=settings.STATIC_ROOT)  # Ahora settings está definido
