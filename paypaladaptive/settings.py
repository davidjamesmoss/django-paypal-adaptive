'''
Created on Jun 13, 2011

@author: greg
'''
from django.conf import settings


DEBUG = getattr(settings, "DEBUG", True)

if DEBUG:
    # use sandboxes while in debug mode
    PAYPAL_ENDPOINT = 'https://svcs.sandbox.paypal.com/AdaptivePayments/'
    PAYPAL_PAYMENT_HOST = 'https://www.sandbox.paypal.com/au/cgi-bin/webscr'
    EMBEDDED_ENDPOINT = 'https://www.sandbox.paypal.com/webapps/adaptivepayment/flow/pay'

    PAYPAL_APPLICATION_ID = 'APP-80W284485P519543T' # sandbox only
else: 
    PAYPAL_ENDPOINT = 'https://svcs.paypal.com/AdaptivePayments/' # production
    PAYPAL_PAYMENT_HOST = 'https://www.paypal.com/webscr' # production
    EMBEDDED_ENDPOINT = 'https://paypal.com/webapps/adaptivepayment/flow/pay'

    PAYPAL_APPLICATION_ID = settings.PAYPAL_APPLICATION_ID

# These settins are required
PAYPAL_USERID = settings.PAYPAL_USERID
PAYPAL_PASSWORD = settings.PAYPAL_PASSWORD
PAYPAL_SIGNATURE = settings.PAYPAL_SIGNATURE
PAYPAL_EMAIL = settings.PAYPAL_EMAIL

USE_CHAIN = getattr(settings, 'PAYPAL_USE_CHAIN', False)
USE_IPN = getattr(settings, 'PAYPAL_USE_IPN', True)
USE_EMBEDDED = getattr(settings, 'PAYPAL_USE_EMBEDDED', True)
SHIPPING = getattr(settings, 'PAYPAL_USE_SHIPPING', False)

COMMISSION_EMAIL = getattr(settings, 'PAYPAL_COMMISSION_EMAIL', False)

