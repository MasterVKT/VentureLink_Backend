import environ

env = environ.Env()
# Lecture du fichier .env si existant
environ.Env.read_env()

# My-CoolPay Configuration
MYCOOLPAY_SANDBOX_PUBLIC_KEY = env('MYCOOLPAY_SANDBOX_PUBLIC_KEY', default='sandbox_public_key_test')
MYCOOLPAY_SANDBOX_PRIVATE_KEY = env('MYCOOLPAY_SANDBOX_PRIVATE_KEY', default='sandbox_private_key_test')
MYCOOLPAY_PUBLIC_KEY = env('MYCOOLPAY_PUBLIC_KEY', default='')
MYCOOLPAY_PRIVATE_KEY = env('MYCOOLPAY_PRIVATE_KEY', default='')

# Site URL pour les callbacks
SITE_URL = env('SITE_URL', default='http://localhost:8000') 

