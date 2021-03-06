DEBUG = True
SECRET_KEY = '9&tb6e%7sgzbi5lj98*!mjpsqxpakpug!8adzj16)4wpebc34&'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'ci.sqlite3',
    }
}

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap3',
    'bulstyle',
    'crispy_forms',
    'model_utils',
    'etd_app',
    'tests',
)

AUTHENTICATION_BACKENDS = (
    'shibboleth.backends.ShibbolethRemoteUserBackend',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'shibboleth.middleware.ShibbolethRemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.messages.context_processors.messages',
                'django.contrib.auth.context_processors.auth',
            ]
        }
    },
]

USE_TZ = True
ROOT_URLCONF = 'tests.test_urlconf'
LOGIN_URL = 'login'
OWNER_ID = 'OWNER_ID'
PUBLIC_DISPLAY_IDENTITY = 'PUBLIC'
EMBARGOED_DISPLAY_IDENTITY = 'EMBARGO'
POST_IDENTITY = 'POST'
AUTHORIZATION_CODE = 'CODE'
FAST_LOOKUP_BASE_URL = 'http://fast.oclc.org/searchfast/fastsuggest'
MEDIA_ROOT = 'media'
STATIC_URL = '/etd_app/static/'
SERVER_ROOT = 'http://localhost'
GRADSCHOOL_ETD_ADDRESS = 'test@localhost'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'etd': {
            'handlers': ['console'],
            'level': 'CRITICAL',
            'propagate': True,
        },
    }
}
