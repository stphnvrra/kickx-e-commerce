"""
PayPal Configuration Settings
"""
import os

# PayPal Configuration
PAYPAL_CLIENT_ID = 'AaHF2aq2vTkFp6_GQWIYCCiA3nS7BLEEKFhstroztRD1YGCXHtB2YLBuYG3i50o7O2MDryfWxd9gESQL'
PAYPAL_CLIENT_SECRET = 'ECO0xX_6Jb7M2uQctvZVtQbVWtjeDUwyps6VIlnkHzMaSfShTlOSSeoZH9awqwc0r4pp5xhAmoZZNzb9'
PAYPAL_MODE = 'live'  # Changed from 'sandbox' to 'live' for production

# API URLs
PAYPAL_API_BASE_URL = 'https://api-m.paypal.com'
PAYPAL_JS_SDK_URL = f'https://www.paypal.com/sdk/js?client-id={PAYPAL_CLIENT_ID}&currency=PHP'

# Order configuration
PAYPAL_RETURN_URL = 'checkout_success'
PAYPAL_CANCEL_URL = 'checkout_payment'

# Currency and locale settings
PAYPAL_CURRENCY = 'PHP'  # Changed to PHP for Philippine region
PAYPAL_LOCALE = 'en_US'  # US English

def get_paypal_config():
    """
    Returns PayPal configuration settings
    """
    return {
        'client_id': PAYPAL_CLIENT_ID,
        'client_secret': PAYPAL_CLIENT_SECRET,
        'mode': PAYPAL_MODE,
        'api_base_url': PAYPAL_API_BASE_URL,
        'js_sdk_url': PAYPAL_JS_SDK_URL,
        'return_url': PAYPAL_RETURN_URL,
        'cancel_url': PAYPAL_CANCEL_URL,
        'currency': PAYPAL_CURRENCY,
        'locale': PAYPAL_LOCALE
    } 