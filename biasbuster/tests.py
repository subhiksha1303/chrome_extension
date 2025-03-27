from django.test import TestCase

# Create your tests here.
import django
django.setup()

from django.apps import apps
print(apps.get_app_configs())
