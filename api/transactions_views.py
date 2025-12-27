from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.conf import settings
from .models import AdminSettings, BuyOrder, Transaction, Vendor
from .vendor_views import get_vendor
import secrets
import requests

def get_rates():
    s = AdminSettings.objects.order_by('-last_updated').first()
    return (float(s.buy_rate) if s and s.buy_rate is not None else 15.2,
            float(s.sell_rate) if s and s.sell_rate is not None else 14.8)

class BuyQuoteView(APIView):
    def post(self, request):
        amount = float(request.data.get('amount_ghs') or 0)
        buy_rate, _ = get_rates()
        usdt = amount / buy_rate if buy_rate > 0 else 0
        return Response({'success': True, 'amount_ghs': amount, 'rate': buy_rate, 'usdt_amount': round(usdt,2)})

class BuyConfirmView(APIView):
    def post(self, request):
        # Get request data
        asset_id = request.data.get('asset_id')
        amount_ghs = float(request.data.get('amount_ghs') or 0)
        recipient_address = request.data.get('recipient_address')
        vendor_email = request.data.get('vendor_email')
        
        # Get asset
        from .models import Asset
        asset = Asset.objects.filter(id=asset_id, buy_enabled=True).first()
        if not asset:
            return Response({'success': False, 'detail': 'Invalid asset'}, status=400)
        
        # Calculate with asset-specific rates and fees
        buy_rate = float(asset.buy_rate) if asset.buy_rate else 15.20
        fee_percent = float(asset.buy_fee_percent) if asset.buy_fee_percent else 1.5
        network_fee_usd = float(asset.network_fee_usd) if asset.network_fee_usd else 0
        
        # Calculate amounts
        crypto_amount = amount_ghs / buy_rate if buy_rate > 0 else 0
        service_fee_ghs = amount_ghs * (fee_percent / 100)
        network_fee_ghs = network_fee_usd * buy_rate
        total_ghs = amount_ghs + service_fee_ghs + network_fee_ghs
        
        # Generate order ID
        order_id = 'CVP-BUY-' + secrets.token_hex(4).upper()
        
        # Create buy order with new status fields
        b = BuyOrder(
            order_id=order_id,
            asset=asset,
            asset_symbol=asset.symbol,
            amount_ghs=amount_ghs,
            rate_usd_to_ghs=buy_rate,
            usdt_amount=crypto_amount,
            fee_percent=fee_percent,
            fee_ghs=service_fee_ghs,
            network_fee_ghs=network_fee_ghs,
            total_charge_ghs=total_ghs,
            network=asset.network,
            recipient_address=recipient_address,
            status='pending',
            payment_status='pending',
            delivery_status='pending'
        )
        b.save()
        
        # Also create transaction record for compatibility
        try:
            current_vendor = get_vendor(request)
            v = current_vendor or (Vendor.objects.filter(email=vendor_email).first() if vendor_email else None) or Vendor.objects.first()
            t = Transaction(
                payment_id=order_id,
                type='buy',
                vendor=v,
                crypto_amount=crypto_amount,
                crypto_symbol=asset.symbol,
                network=asset.network,
                wallet_address=recipient_address,
                customer_email=(current_vendor.email if current_vendor else vendor_email),
                fiat_amount=amount_ghs,
                exchange_rate=buy_rate,
                rate_used=buy_rate,
                coinvibe_fee=service_fee_ghs,
                network_fee=network_fee_ghs,
                status='pending',
            )
            t.save()
        except Exception:
            pass
        
        return Response({'success': True, 'order_id': order_id, 'total_ghs': total_ghs})

class BuyPaystackInitView(APIView):
    def post(self, request):
        order_id = request.data.get('order_id')
        email = request.data.get('email')
        b = BuyOrder.objects.filter(order_id=order_id).first()
        if not b:
            return Response({'detail': 'order_not_found'}, status=404)
        if not email:
            return Response({'detail': 'email_required'}, status=400)
        secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        base = getattr(settings, 'PAYSTACK_BASE_URL', 'https://api.paystack.co')
        if not secret:
            return Response({'detail': 'paystack_not_configured'}, status=500)
        try:
            payload = {
                'email': email,
                'amount': int(round(b.total_charge_ghs * 100)),
                'currency': 'GHS',
                'reference': b.order_id,
                'callback_url': request.build_absolute_uri('/paystack/callback'),
            }
            res = requests.post(f"{base}/transaction/initialize", json=payload, headers={
                'Authorization': f"Bearer {secret}",
                'Content-Type': 'application/json',
            }, timeout=20)
            data = res.json()
            if res.status_code != 200 or not data.get('status'):
                return Response({'detail': data.get('message') or 'paystack_error'}, status=502)
            return Response({'success': True, 'authorization_url': data['data']['authorization_url'], 'reference': data['data']['reference']})
        except Exception as e:
            return Response({'detail': 'paystack_init_failed'}, status=502)

class PaystackWebhookView(APIView):
    def post(self, request):
        raw = request.body
        secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        import hmac, hashlib
        signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
        if not signature or not secret:
            return Response({'detail': 'unauthorized'}, status=401)
        computed = hmac.new(secret.encode('utf-8'), raw, hashlib.sha512).hexdigest()
        if not hmac.compare_digest(signature, computed):
            return Response({'detail': 'invalid_signature'}, status=401)
        try:
            payload = request.data
            event = payload.get('event')
            data = payload.get('data') or {}
            reference = data.get('reference')
            if event == 'charge.success' and reference:
                b = BuyOrder.objects.filter(order_id=reference).first()
                if b:
                    b.payment_status = 'paid'
                    b.paid_at = timezone.now()
                    b.status = 'processing'  # Move to processing, waiting for delivery
                    b.paystack_reference = reference
                    b.save()
                t = Transaction.objects.filter(payment_id=reference, type='buy').first()
                if t:
                    t.status = 'processing'  # Don't mark completed until delivery
                    t.save()
            return Response({'success': True})
        except Exception:
            return Response({'detail': 'webhook_error'}, status=400)

class BuyGetView(APIView):
    def get(self, request, order_id: str):
        b = BuyOrder.objects.filter(order_id=order_id).first()
        if not b:
            return Response({'detail':'not_found'}, status=404)
        return Response({'success': True, 'order': {
            'order_id': b.order_id,
            'amount_ghs': b.amount_ghs,
            'usdt_amount': b.usdt_amount,
            'network': b.network,
            'recipient_address': b.recipient_address,
            'status': b.status,
        }})

class SellQuoteView(APIView):
    def post(self, request):
        usdt = float(request.data.get('usdt_amount') or 0)
        _, sell_rate = get_rates()
        ghs = usdt * sell_rate
        fee = ghs * 0.015
        total = ghs - fee
        return Response({'success': True, 'usdt_amount': usdt, 'rate': sell_rate, 'fee': round(fee,2), 'amount_ghs': round(total,2)})

class SellConfirmView(APIView):
    def post(self, request):
        usdt = float(request.data.get('usdt_amount') or 0)
        network = request.data.get('network')
        wallet_address = request.data.get('wallet_address')
        vendor_email = request.data.get('vendor_email')
        current_vendor = get_vendor(request)
        tx_hash = (request.data.get('tx_hash') or '').strip()
        customer_email = request.data.get('customer_email')
        v = current_vendor or Vendor.objects.filter(email=vendor_email).first()
        _, sell_rate = get_rates()
        ghs = usdt * sell_rate
        fee = ghs * 0.015
        total = ghs - fee
        payment_id = 'CVP-SELL-' + secrets.token_hex(4).upper()
        t = Transaction(
            payment_id=payment_id,
            type='sell',
            vendor=v if v else Vendor.objects.first(),
            crypto_amount=usdt,
            crypto_symbol='USDT',
            network=network,
            wallet_address=wallet_address,
            customer_email=customer_email or (v.email if v else None),
            fiat_amount=total,
            exchange_rate=sell_rate,
            rate_used=sell_rate,
            coinvibe_fee=fee,
            status='pending',
            crypto_tx_hash=tx_hash or None,
        )
        t.save()
        t.save()
        
        # Send email notification
        from .email_service import send_sell_order_email
        try:
            email = customer_email or (v.email if v else None)
            if email:
                send_sell_order_email(email, {
                    'payment_id': payment_id,
                    'crypto_amount': usdt,
                    'crypto_symbol': 'USDT',
                    'fiat_amount': total,
                    'network': network,
                    'wallet_address': wallet_address
                })
        except Exception:
            pass
            
        return Response({'success': True, 'payment_id': payment_id})

class SellGetView(APIView):
    def get(self, request, payment_id: str):
        t = Transaction.objects.filter(payment_id=payment_id).first()
        if not t:
            return Response({'detail':'not_found'}, status=404)
        return Response({'success': True, 'transaction': {
            'payment_id': t.payment_id,
            'type': t.type,
            'crypto_amount': t.crypto_amount,
            'fiat_amount': t.fiat_amount,
            'network': t.network,
            'status': t.status,
        }})

class BuyPaymentInstructionsView(APIView):
    """Get payment instructions for a buy order"""
    def get(self, request, order_id):
        b = BuyOrder.objects.filter(order_id=order_id).first()
        if not b:
            return Response({'detail': 'Order not found'}, status=404)
        
        if b.payment_status == 'paid':
            return Response({'detail': 'Order already paid'}, status=400)
            
        # Get payment settings
        from .models import ExchangePaymentSettings
        settings = ExchangePaymentSettings.objects.order_by('-last_updated').first()
        
        if not settings:
            settings = ExchangePaymentSettings.objects.create()
            
        instructions = {
            'amount_ghs': b.total_charge_ghs,
            'reference': b.order_id,
            'mobile_money': {
                'number': settings.ghs_momo_number or 'Not configured',
                'name': settings.ghs_momo_name or 'Not configured',
                'network': settings.ghs_momo_network or 'MTN',
            },
            'bank_transfer': {
                'bank_name': settings.ghs_bank_name or 'Not configured',
                'account_number': settings.ghs_account_number or 'Not configured',
                'account_name': settings.ghs_account_name or 'Not configured',
            }
        }
        
        return Response({
            'success': True,
            'order_id': order_id,
            'instructions': instructions
        })

class BuyConfirmPaymentView(APIView):
    """Confirm payment for a buy order"""
    def post(self, request, order_id):
        payment_reference = request.data.get('payment_reference')
        
        b = BuyOrder.objects.filter(order_id=order_id).first()
        if not b:
            return Response({'detail': 'Order not found'}, status=404)
            
        if b.payment_status == 'paid':
            return Response({'detail': 'Order already paid'}, status=400)
            
        if not payment_reference:
            return Response({'detail': 'Payment reference is required'}, status=400)
            
        # Update order
        b.payment_reference = payment_reference.strip()
        b.payment_status = 'verification_pending'
        b.paid_at = timezone.now()
        b.status = 'processing' # Move to processing
        b.save()
        
        # Update associated transaction if exists
        t = Transaction.objects.filter(payment_id=order_id, type='buy').first()
        if t:
            t.status = 'processing'
            t.save()
            
        # Send email notification
        from .email_service import send_buy_order_email
        try:
            # Get user email - either from transaction or vendor
            email = None
            if t and t.customer_email:
                email = t.customer_email
            elif b.asset: # Just a check to ensure b exists
                # Try to get vendor email
                v = Vendor.objects.filter(email=request.user.email if request.user.is_authenticated else '').first()
                if v:
                    email = v.email
            
            if email:
                send_buy_order_email(email, {
                    'order_id': b.order_id,
                    'amount_ghs': b.amount_ghs,
                    'asset_symbol': b.asset_symbol,
                    'network': b.network,
                    'recipient_address': b.recipient_address
                })
        except Exception as e:
            print(f"Failed to send email: {e}")
            
        return Response({
            'success': True,
            'message': 'Payment confirmed. Admin will process your order shortly.'
        })