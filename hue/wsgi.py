"""
WSGI config for HUE project.
Exposes the WSGI callable as ``application`` and ``app`` for standard WSGI servers and Vercel.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hue.settings')

application = get_wsgi_application()
app = application
