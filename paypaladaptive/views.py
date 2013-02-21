'''
Paypal Adaptive Payments supporting views

Created on Jun 13, 2011

@author: greg
'''
from api import IpnError
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponseServerError, Http404, \
    HttpResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from models import Payment, Preapproval
import api
import logging
import settings
from django.http import HttpResponseRedirect
from signals import ipn_confirmed, ipn_refunded

logger = logging.getLogger(__name__)

#@login_required
@transaction.autocommit
def payment_cancel(request, payment_id, payment_secret_uuid, template="paypaladaptive/cancel.html"):
    '''
    Incoming cancellation from paypal
    '''
    logger.debug( "Cancellation received for Payment %s" % payment_id)
    
    try:
        payment = Payment.objects.get(id=payment_id, secret_uuid=payment_secret_uuid)
    except ObjectDoesNotExist:
        raise Http404
    
    if request.user != payment.purchaser:
        return HttpResponseForbidden("Unauthorized")
    
    payment.status = 'canceled'
    payment.save()

    context = RequestContext(request)
    template_vars = {"is_embedded": settings.USE_EMBEDDED}
    
    return HttpResponseRedirect(payment.cancel_redirect_url)
    #return render_to_response(template, template_vars, context)


#@login_required
@transaction.autocommit
def payment_return(request, payment_id, payment_secret_uuid, template="paypaladaptive/return.html"):
    '''
    Incoming return from paypal process (note this is a return to the site, not a returned payment)
    '''
    logger.debug( "Return received for Payment %s" % payment_id)
    
    try:
        payment = Payment.objects.get(id=payment_id, secret_uuid=payment_secret_uuid)
    except ObjectDoesNotExist:
        raise Http404
    '''
    if request.user != payment.purchaser:
        return HttpResponseForbidden("Unauthorized")
    
    if payment.status not in ['created', 'completed']:
        payment.status_detail = 'Expected status to be created or completed, not %s - duplicate transaction?' % payment.status
        payment.status = 'error'
        payment.save()
        return HttpResponseServerError('Unexpected error')

    elif payment_secret_uuid != payment.secret_uuid:
        payment.status_detail = 'BuyReturn secret "%s" did not match' % payment_secret_uuid
        payment.status = 'error'
        payment.save()
        return HttpResponseServerError('Unexpected error')

    if payment.status != 'completed':
        payment.status = 'returned'
        payment.save()
        
    if not settings.USE_IPN:
        # TODO: make PaymentDetails call here if not using IPN
        pass
    
    context = RequestContext(request)
    template_vars = {"is_embedded": settings.USE_EMBEDDED}
    return render_to_response(template, template_vars, context)
    '''
    
    return HttpResponseRedirect(payment.return_redirect_url)


@login_required
@transaction.autocommit
def preapproval_cancel(request, preapproval_id, preapproval_secret_uuid, template="paypaladaptive/cancel.html"):
    '''
    Incoming preapproval cancellation from paypal
    '''
    logger.debug( "Cancellation received for Preapproval %s" % preapproval_id)
    
    try:
        preapproval = Preapproval.objects.get(id=preapproval_id)
    except ObjectDoesNotExist:
        raise Http404
    
    if request.user != preapproval.purchaser:
        return HttpResponseForbidden("Unauthorized")
    
    preapproval.status = 'canceled'
    preapproval.save()

    context = RequestContext(request)
    template_vars = {"is_embedded": settings.USE_EMBEDDED}
        
    return render_to_response(template, template_vars, context)


@login_required
@transaction.autocommit
def preapproval_return(request, preapproval_id, preapproval_secret_uuid, template="paypaladaptive/return.html"):
    '''
    Incoming return from paypal process (note this is a return to the site, not a returned payment)
    '''
    logger.debug( "Return received for Payment %s" % preapproval_id)
    
    try:
        preapproval = Preapproval.objects.get(id=preapproval_id)
    except ObjectDoesNotExist:
        raise Http404
    
    if request.user != preapproval.purchaser:
        return HttpResponseForbidden("Unauthorized")
    
    if preapproval.status not in ['created', 'completed']:
        preapproval.status_detail = 'Expected status to be created or completed, not %s - duplicate transaction?' % preapproval.status
        preapproval.status = 'error'
        preapproval.save()
        return HttpResponseServerError('Unexpected error')

    elif preapproval_secret_uuid != preapproval.secret_uuid:
        preapproval.status_detail = 'BuyReturn secret "%s" did not match' % preapproval_secret_uuid
        preapproval.status = 'error'
        preapproval.save()
        return HttpResponseServerError('Unexpected error')

    if preapproval.status != 'completed':
        preapproval.status = 'returned'
        preapproval.save()
        
    if not settings.USE_IPN:
        # TODO: make PaymentDetails call here if not using IPN
        pass
    
    context = RequestContext(request)
    template_vars = {"is_embedded": settings.USE_EMBEDDED}
        
    return render_to_response(template, template_vars, context)


@require_POST
@csrf_exempt
@transaction.autocommit
def payment_ipn(request, payment_id, payment_secret_uuid):
    '''
    Incoming IPN POST request from Paypal
    '''
    logger.debug("IPN received for Payment %s" % payment_id)
    
    try:
        ipn = api.IPN(request)
    except IpnError, e:
        logger.warning("PayPal IPN verify failed: %s" % e)
        logger.debug("Request was: %s" % request)
        return HttpResponse('verify failed', status=200)
         
    try:
        payment = Payment.objects.get(id=payment_id)
    except ObjectDoesNotExist:
        logger.warning('Could not find Payment ID %s, replying to IPN with 404.' % payment_id)
        raise Http404
    
    if payment.secret_uuid != payment_secret_uuid:
        payment.status = 'error'
        payment.status_detail = 'IPN secret "%s" did not match' % payment_secret_uuid
        payment.save()
        return HttpResponse('secret mismatch', status=200)
    
    # Type of IPN?
    if ipn.type == api.IPN_TYPE_PAYMENT:
        payment.transaction_id = ipn.transactions[0].id
        
        if payment.amount != ipn.transactions[0].amount:
            payment.status = 'error'
            payment.status_detail = "IPN amounts didn't match. Payment requested %s. Payment made %s" % \
                (payment.amount, ipn.transactions[0].amount)
        else:
            payment.status = 'completed'

    elif ipn.type == api.IPN_TYPE_ADJUSTMENT:
        payment.status = 'refunded'
        
    elif ipn.type == api.IPN_TYPE_PREAPPROVAL:
        # TODO:
        logger.error('IPN preapproval request is not implemented!')
        raise NotImplementedError        

    payment.save()
    
    if payment.status == 'completed':
        logger.debug("Sending Payment Completed Signal")
        ipn_confirmed.send(sender=None, payment=payment)
    elif payment.status == 'refunded':
        ipn_refunded.send(sender=None, payment=payment)
    
    # Ok, no content
    return HttpResponse('Received.', status=200)
