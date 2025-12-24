from django.views import View
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.conf import settings
import requests
from api.models import BuyOrder, Transaction, Vendor
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib import messages
from .forms import VendorPasswordResetForm, VendorSetPasswordForm
from .tokens import vendor_token_generator


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

class BuyManualSuccessView(TemplateView):
    template_name = 'buy_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reference = self.request.GET.get('reference') or '--'
        # For manual payment, we assume success if they got here
        context['success'] = True
        context['status'] = 'Pending Verification'
        context['reference'] = reference
        return context

class VendorPasswordResetView(FormView):
    template_name = 'registration/password_reset_form.html'
    form_class = VendorPasswordResetForm
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': vendor_token_generator,
            'from_email': None,
            'email_template_name': 'registration/password_reset_email.txt',
            'html_email_template_name': 'registration/password_reset_email.html',
            'subject_template_name': 'registration/password_reset_subject.txt',
            'request': self.request,
        }
        form.save(**opts)
        return super().form_valid(form)

class VendorPasswordResetDoneView(TemplateView):
    template_name = 'registration/password_reset_done.html'

class VendorPasswordResetConfirmView(FormView):
    template_name = 'registration/password_reset_confirm.html'
    form_class = VendorSetPasswordForm
    success_url = reverse_lazy('password_reset_complete')

    def dispatch(self, *args, **kwargs):
        assert 'uidb64' in kwargs and 'token' in kwargs

        self.validlink = False
        self.vendor = self.get_user(kwargs['uidb64'])

        if self.vendor is not None:
            token = kwargs['token']
            if vendor_token_generator.check_token(self.vendor, token):
                self.validlink = True
                return super().dispatch(*args, **kwargs)

        # Display the "password reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            vendor = Vendor.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Vendor.DoesNotExist):
            vendor = None
        return vendor

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['vendor'] = self.vendor
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.validlink:
            context['validlink'] = True
        else:
            context.update({
                'form': None,
                'title': 'Password reset unsuccessful',
                'validlink': False,
            })
        return context

class VendorPasswordResetCompleteView(TemplateView):
    template_name = 'registration/password_reset_complete.html'

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