from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import Transaction, Vendor
import secrets

class PaymentCreateView(APIView):
    def post(self, request):
        vendor_email = request.data.get('vendor_email')
        amount = float(request.data.get('amount_ghs') or 0)
        v = Vendor.objects.filter(email=vendor_email).first()
        payment_id = 'CVP-PAY-' + secrets.token_hex(4).upper()
        t = Transaction(payment_id=payment_id, type='buy', vendor=v if v else Vendor.objects.first(), crypto_amount=0, fiat_amount=amount, status='pending', network='MOMO', wallet_address='')
        t.save()
        return Response({'success': True, 'payment_id': payment_id})

class PaymentGetView(APIView):
    def get(self, request, payment_id: str):
        t = Transaction.objects.filter(payment_id=payment_id).first()
        if not t:
            return Response({'detail':'not_found'}, status=404)
        return Response({'success': True, 'payment': {
            'payment_id': t.payment_id,
            'type': t.type,
            'fiat_amount': t.fiat_amount,
            'status': t.status,
        }})