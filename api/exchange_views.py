from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from .models import ExchangeRate, CurrencyExchange, Vendor
from .vendor_views import get_vendor
import secrets
import requests

class ExchangeQuoteView(APIView):
    """Get a quote for currency exchange"""
    def post(self, request):
        from_currency = request.data.get('from_currency', '').upper()
        to_currency = request.data.get('to_currency', '').upper()
        amount = float(request.data.get('amount', 0))
        
        if from_currency not in ['NGN', 'GHS'] or to_currency not in ['NGN', 'GHS']:
            return Response({'detail': 'Invalid currency'}, status=400)
        
        if from_currency == to_currency:
            return Response({'detail': 'Same currency'}, status=400)
        
        # Get current exchange rates
        rate_obj = ExchangeRate.objects.order_by('-last_updated').first()
        if not rate_obj:
            return Response({'detail': 'Exchange rates not configured'}, status=500)
        
        
        # Validate amount limits (skip for small amounts used for rate preview)
        if amount > 10:  # Only validate if amount is significant
            if from_currency == 'GHS':
                if amount < rate_obj.min_exchange_ghs or amount > rate_obj.max_exchange_ghs:
                    return Response({
                        'detail': f'Amount must be between ₵{rate_obj.min_exchange_ghs} and ₵{rate_obj.max_exchange_ghs}'
                    }, status=400)
                rate = rate_obj.ghs_to_ngn_rate
            else:  # NGN
                if amount < rate_obj.min_exchange_ngn or amount > rate_obj.max_exchange_ngn:
                    return Response({
                        'detail': f'Amount must be between ₦{rate_obj.min_exchange_ngn} and ₦{rate_obj.max_exchange_ngn}'
                    }, status=400)
                rate = rate_obj.ngn_to_ghs_rate
        else:
            # For preview/rate display, just get the rate without validation
            if from_currency == 'GHS':
                rate = rate_obj.ghs_to_ngn_rate
            else:
                rate = rate_obj.ngn_to_ghs_rate
        
        # Calculate exchange
        gross_amount = amount * rate
        fee = gross_amount * (rate_obj.fee_percent / 100)
        net_amount = gross_amount - fee
        
        return Response({
            'success': True,
            'quote': {
                'from_currency': from_currency,
                'to_currency': to_currency,
                'from_amount': amount,
                'to_amount': round(net_amount, 2),
                'exchange_rate': rate,
                'fee_percent': rate_obj.fee_percent,
                'fee_amount': round(fee, 2),
                'gross_amount': round(gross_amount, 2),
            }
        })

class ExchangeCreateView(APIView):
    """Create a new currency exchange order"""
    def post(self, request):
        v = get_vendor(request)
        if not v:
            return Response({'detail': 'unauthorized'}, status=401)
        
        from_currency = request.data.get('from_currency', '').upper()
        to_currency = request.data.get('to_currency', '').upper()
        from_amount = float(request.data.get('from_amount', 0))
        recipient_details = request.data.get('recipient_details', {})
        
        # Get exchange rates
        rate_obj = ExchangeRate.objects.order_by('-last_updated').first()
        if not rate_obj:
            return Response({'detail': 'Exchange rates not configured'}, status=500)
        
        # Calculate exchange
        if from_currency == 'GHS':
            rate = rate_obj.ghs_to_ngn_rate
        else:
            rate = rate_obj.ngn_to_ghs_rate
        
        gross_amount = from_amount * rate
        fee = gross_amount * (rate_obj.fee_percent / 100)
        net_amount = gross_amount - fee
        
        # Create exchange order
        exchange_id = f'CVP-EXC-{secrets.token_hex(4).upper()}'
        exchange = CurrencyExchange(
            exchange_id=exchange_id,
            vendor=v,
            from_currency=from_currency,
            to_currency=to_currency,
            from_amount=from_amount,
            to_amount=round(net_amount, 2),
            exchange_rate=rate,
            fee_amount=round(fee, 2),
            recipient_details=recipient_details,
            status='pending_payment'
        )
        exchange.save()
        
        return Response({
            'success': True,
            'exchange': {
                'exchange_id': exchange_id,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'from_amount': from_amount,
                'to_amount': round(net_amount, 2),
                'fee_amount': round(fee, 2),
                'status': 'pending_payment'
            }
        }, status=201)

class ExchangeGetView(APIView):
    """Get details of a specific exchange"""
    def get(self, request, exchange_id):
        v = get_vendor(request)
        if not v:
            return Response({'detail': 'unauthorized'}, status=401)
        
        exchange = CurrencyExchange.objects.filter(exchange_id=exchange_id, vendor=v).first()
        if not exchange:
            return Response({'detail': 'Exchange not found'}, status=404)
        
        return Response({
            'success': True,
            'exchange': {
                'exchange_id': exchange.exchange_id,
                'from_currency': exchange.from_currency,
                'to_currency': exchange.to_currency,
                'from_amount': exchange.from_amount,
                'to_amount': exchange.to_amount,
                'exchange_rate': exchange.exchange_rate,
                'fee_amount': exchange.fee_amount,
                'recipient_details': exchange.recipient_details,
                'payment_reference': exchange.payment_reference,
                'status': exchange.status,
                'created_at': exchange.created_at.isoformat(),
                'paid_at': exchange.paid_at.isoformat() if exchange.paid_at else None,
                'completed_at': exchange.completed_at.isoformat() if exchange.completed_at else None,
            }
        })

class ExchangePaymentInstructionsView(APIView):
    """Get payment instructions for currency exchange"""
    def get(self, request, exchange_id):
        v = get_vendor(request)
        if not v:
            return Response({'detail': 'unauthorized'}, status=401)
        
        exchange = CurrencyExchange.objects.filter(exchange_id=exchange_id, vendor=v).first()
        if not exchange:
            return Response({'detail': 'Exchange not found'}, status=404)
        
        if exchange.status != 'pending_payment':
            return Response({'detail': 'Exchange already processed'}, status=400)
        
        # Get payment settings from database
        from .models import ExchangePaymentSettings
        settings = ExchangePaymentSettings.objects.order_by('-last_updated').first()
        
        if not settings:
            # Create default settings if none exist
            settings = ExchangePaymentSettings.objects.create()
        
        # Get payment instructions based on currency
        instructions = {}
        
        if exchange.from_currency == 'NGN':
            # Nigerian Naira payment instructions
            instructions = {
                'currency': 'NGN',
                'amount': float(exchange.from_amount),
                'payment_method': 'bank_transfer',
                'bank_name': settings.ngn_bank_name or 'Not configured',
                'account_number': settings.ngn_account_number or 'Not configured',
                'account_name': settings.ngn_account_name or 'Not configured',
                'reference': exchange.exchange_id,
                'instructions': [
                    f'Transfer ₦{exchange.from_amount:,.2f} to the account above',
                    'Use the exchange ID as your transfer reference',
                    'After payment, upload proof or note the transaction reference',
                    'Your exchange will be processed within 30 minutes of confirmation'
                ]
            }
        elif exchange.from_currency == 'GHS':
            # Ghana Cedis payment instructions
            instructions = {
                'currency': 'GHS',
                'amount': float(exchange.from_amount),
                'payment_method': 'mobile_money',
                'momo_number': settings.ghs_momo_number or 'Not configured',
                'momo_name': settings.ghs_momo_name or 'Not configured',
                'momo_network': settings.ghs_momo_network or 'MTN',
                'reference': exchange.exchange_id,
                'instructions': [
                    f'Send GH₵{exchange.from_amount:,.2f} to the MoMo number above',
                    'Use the exchange ID as your reference/description',
                    'After payment, note down the MoMo transaction reference',
                    'Confirm payment with the transaction reference',
                    'Your exchange will be processed within 30 minutes of confirmation'
                ]
            }
        
        return Response({
            'success': True,
            'exchange_id': exchange_id,
            'payment_instructions': instructions
        })

class ExchangeConfirmPaymentView(APIView):
    """Confirm payment for currency exchange (both NGN and GHS)"""
    def post(self, request, exchange_id):
        payment_reference = request.data.get('payment_reference')  # Can be MoMo ref or bank transfer ref
        
        v = get_vendor(request)
        if not v:
            return Response({'detail': 'unauthorized'}, status=401)
        
        exchange = CurrencyExchange.objects.filter(exchange_id=exchange_id, vendor=v).first()
        if not exchange:
            return Response({'detail': 'Exchange not found'}, status=404)
        
        if exchange.status != 'pending_payment':
            return Response({'detail': 'Exchange already processed'}, status=400)
        
        if not payment_reference:
            return Response({'detail': 'Payment reference is required'}, status=400)
        
        # Update exchange with payment reference and mark as paid
        exchange.payment_reference = payment_reference.strip()
        exchange.status = 'paid'
        exchange.paid_at = timezone.now()
        exchange.save()
        
        # Send email notification
        from .email_service import send_exchange_order_email
        try:
            email = exchange.vendor.email
            if email:
                send_exchange_order_email(email, {
                    'exchange_id': exchange.exchange_id,
                    'from_amount': exchange.from_amount,
                    'from_currency': exchange.from_currency,
                    'to_amount': exchange.to_amount,
                    'to_currency': exchange.to_currency,
                    'exchange_rate': exchange.exchange_rate
                })
        except Exception:
            pass
        
        return Response({
            'success': True,
            'message': 'Payment confirmed. Admin will process your exchange shortly.'
        })
