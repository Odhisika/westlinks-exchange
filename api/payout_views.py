from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction as dbtx
from .models import Vendor, Transaction
from payments.paystack import create_recipient, initiate_transfer, verify_transfer

class CreateRecipientView(APIView):
    def post(self, request):
        email = request.data.get('email')
        v = Vendor.objects.filter(email=email).first()
        if not v:
            return Response({'detail':'vendor_not_found'}, status=404)
        if v.paystack_recipient_code:
            return Response({'success': True, 'recipient_code': v.paystack_recipient_code})
        code, body = create_recipient(v.name, v.email, v.momo_number)
        if code == 201 and body.get('status'):
            v.paystack_recipient_code = body['data']['recipient_code'] if 'data' in body and 'recipient_code' in body['data'] else body['data'].get('code')
            v.save()
            return Response({'success': True, 'recipient_code': v.paystack_recipient_code})
        return Response({'detail':'paystack_error', 'body': body}, status=400)

class InitiateTransferView(APIView):
    def post(self, request):
        payment_id = request.data.get('payment_id')
        t = Transaction.objects.filter(payment_id=payment_id).first()
        if not t:
            return Response({'detail':'transaction_not_found'}, status=404)
        v = t.vendor
        if not v.paystack_recipient_code:
            return Response({'detail':'missing_recipient_code'}, status=400)
        code, body = initiate_transfer(t.fiat_amount or 0, v.paystack_recipient_code, f'Payout {payment_id}')
        if code in (200, 201) and body.get('status'):
            data = body.get('data') or {}
            t.transfer_code = data.get('transfer_code') or data.get('reference') or t.transfer_code
            t.payout_status = 'processing'
            t.save()
            return Response({'success': True, 'transfer_code': t.transfer_code})
        return Response({'detail':'paystack_error', 'body': body}, status=400)

class VerifyTransferView(APIView):
    def post(self, request):
        reference = request.data.get('reference')
        code, body = verify_transfer(reference)
        if code == 200 and body.get('status'):
            status_text = body.get('data', {}).get('status')
            return Response({'success': True, 'status': status_text})
        return Response({'detail':'verification_failed', 'body': body}, status=400)

class PaystackWebhookView(APIView):
    def post(self, request):
        event = request.data.get('event')
        data = request.data.get('data') or {}
        if event == 'transfer.success':
            ref = data.get('reference') or data.get('transfer_code')
            if ref:
                t = Transaction.objects.filter(transfer_code=ref).first()
                if t:
                    t.payout_status = 'success'
                    t.status = 'completed'
                    t.completed_at = timezone.now()
                    t.save()
        elif event == 'transfer.failed':
            ref = data.get('reference') or data.get('transfer_code')
            if ref:
                t = Transaction.objects.filter(transfer_code=ref).first()
                if t:
                    t.payout_status = 'failed'
                    t.save()
        return Response({'ok': True})