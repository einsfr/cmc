import os

from cmc.settings import BASE_DIR


# RENAME THIS FILE TO local.py TO USE IT IN PROJECT

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'my-very-secret-key'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
