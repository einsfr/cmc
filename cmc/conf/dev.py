ALLOWED_HOSTS = []


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


INSTALLED_APPS = [
    'debug_toolbar',
]


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer', 'rest_framework.renderers.BrowsableAPIRenderer'
    )
}