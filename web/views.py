from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import render
from django.conf import settings
import requests
from api.models import BuyOrder, Transaction, Vendor
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

@method_decorator(never_cache, name='dispatch')
class ProtectedTemplateView(TemplateView):
    """
    A TemplateView that prevents caching.
    This ensures that when a user logs out and clicks 'back',
    the browser is forced to reload the page, triggering the JS auth check.
    """
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

class PaystackCallbackView(View):
    def get(self, request):
        reference = request.GET.get('reference') or request.GET.get('ref')
        secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        base = getattr(settings, 'PAYSTACK_BASE_URL', 'https://api.paystack.co')
        success = False
        status = 'failed'
        if reference and secret:
            try:
                res = requests.get(f"{base}/transaction/verify/{reference}", headers={
                    'Authorization': f"Bearer {secret}"
                }, timeout=20)
                data = res.json()
                ok = res.status_code == 200 and data.get('status') and (data.get('data') or {}).get('status') == 'success'
                success = bool(ok)
                status = 'completed' if ok else 'failed'
                payload_data = (data.get('data') or {})
                customer_email = ((payload_data.get('customer') or {}).get('email'))
                b = BuyOrder.objects.filter(order_id=reference).first()
                if b:
                    b.status = status
                    if ok:
                        b.completed_at = timezone.now()
                    b.save()
                    t = Transaction.objects.filter(payment_id=reference, type='buy').first()
                    if t:
                        t.status = status
                        if ok:
                            t.completed_at = timezone.now()
                        t.save()
                    else:
                        v = Vendor.objects.filter(email=customer_email).first() or Vendor.objects.first()
                        t = Transaction(
                            payment_id=reference,
                            type='buy',
                            vendor=v,
                            crypto_amount=b.usdt_amount,
                            crypto_symbol='USDT',
                            network=b.network,
                            wallet_address=b.recipient_address,
                            fiat_amount=b.total_charge_ghs,
                            exchange_rate=b.rate_usd_to_ghs,
                            rate_used=b.rate_usd_to_ghs,
                            coinvibe_fee=b.fee_ghs,
                            customer_email=customer_email,
                            status=status,
                        )
                        if ok:
                            t.completed_at = timezone.now()
                        t.save()
            except Exception:
                pass
        ctx = {'reference': reference or '--', 'success': success, 'status': status}
        return render(request, 'buy_success.html', ctx)

@method_decorator(never_cache, name='dispatch')
class ExchangeView(TemplateView):
    template_name = 'exchange/cedis-naira.html'
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response