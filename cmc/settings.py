"""
Django settings for cmc project.

Generated by 'django-admin startproject' using Django 1.10.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
from cmc.conf import import_settings

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_ENV = os.environ.get('APP_ENV', 'prod')

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'crispy_forms',
    'cmcdispatcher',
]

import_settings(
    globals(),
    [r'*@^cmc', 'common', '*{}'.format(APP_ENV), 'local', '*{}-local'],
    INSTALLED_APPS,
    ('INSTALLED_APPS', 'REST_FRAMEWORK')
)
