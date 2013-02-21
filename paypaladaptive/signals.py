from django.dispatch import Signal
ipn_confirmed = Signal(providing_args=['payment'])
ipn_refunded = Signal(providing_args=['payment'])