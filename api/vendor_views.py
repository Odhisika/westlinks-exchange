from django.utils import timezone
from django.db.models import Q, Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password, check_password
from .models import Vendor, VendorSession, Transaction
import secrets
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

def get_vendor(request):
    token = request.headers.get('Authorization') or ''
    token = token.replace('Bearer ','')
    if not token:
        return None
    sess = VendorSession.objects.filter(session_token=token).first()
    if not sess or timezone.now() > sess.expires_at:
        return None
    return sess.vendor

@method_decorator(csrf_exempt, name='dispatch')
class VendorRegisterView(APIView):
    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')
        momo = request.data.get('momo_number')
        if not all([name, email, password, momo]):
            return Response({'detail':'missing_fields'}, status=400)
        if Vendor.objects.filter(email=email).exists():
            return Response({'detail':'email_exists'}, status=400)
        v = Vendor(name=name, email=email, password_hash=make_password(password), momo_number=momo)
        v.save()
        return Response({'success': True, 'vendor': {'id': v.id, 'name': v.name, 'email': v.email, 'momo_number': v.momo_number, 'country': v.country, 'balance': v.balance, 'is_active': v.is_active, 'is_verified': v.is_verified}})

@method_decorator(csrf_exempt, name='dispatch')
class VendorLoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        v = Vendor.objects.filter(email=email).first()
        if not v or not check_password(password, v.password_hash):
            return Response({'detail':'invalid_credentials'}, status=401)
        token = secrets.token_urlsafe(32)
        expires = timezone.now() + timezone.timedelta(hours=24)
        VendorSession.objects.create(vendor=v, session_token=token, expires_at=expires)
        v.last_login = timezone.now()
        v.save()
        return Response({'success': True, 'token': token, 'expires_at': expires.isoformat(), 'vendor': {'id': v.id, 'name': v.name, 'email': v.email, 'momo_number': v.momo_number, 'country': v.country, 'balance': v.balance, 'is_active': v.is_active, 'is_verified': v.is_verified}})

class VendorMeView(APIView):
    def get(self, request):
        v = get_vendor(request)
        if not v:
            return Response({'detail':'unauthorized'}, status=401)
        return Response({'id': v.id, 'name': v.name, 'email': v.email, 'momo_number': v.momo_number, 'country': v.country, 'balance': v.balance, 'is_active': v.is_active, 'is_verified': v.is_verified})
    def put(self, request):
        v = get_vendor(request)
        if not v:
            return Response({'detail':'unauthorized'}, status=401)
        v.name = request.data.get('name', v.name)
        v.momo_number = request.data.get('momo_number', v.momo_number)
        v.country = request.data.get('country', v.country)
        v.save()
        return Response({'success': True})

class VendorPasswordView(APIView):
    def post(self, request):
        v = get_vendor(request)
        if not v:
            return Response({'detail':'unauthorized'}, status=401)
        cur = request.data.get('current_password')
        new = request.data.get('new_password')
        if not check_password(cur, v.password_hash):
            return Response({'detail':'incorrect_password'}, status=400)
        v.password_hash = make_password(new)
        v.save()
        return Response({'success': True})

class VendorTransactionsView(APIView):
    def get(self, request):
        v = get_vendor(request)
        if not v:
            return Response({'detail':'unauthorized'}, status=401)
        
        # Get all transactions for this vendor
        from django.db.models import Q
        
        # Try different filters to find transactions
        by_vendor = Transaction.objects.filter(vendor=v).count()
        by_email = Transaction.objects.filter(customer_email=v.email).count()
        all_trans = Transaction.objects.all().count()
        
        print(f"DEBUG - Vendor: {v.email}")
        print(f"DEBUG - Transactions by vendor FK: {by_vendor}")
        print(f"DEBUG - Transactions by customer_email: {by_email}")
        print(f"DEBUG - Total transactions in DB: {all_trans}")
        
        # Get transactions
        qs = Transaction.objects.filter(vendor=v).order_by('-created_at')[:500]
        
        data = [
            {
                'payment_id': t.payment_id,
                'type': t.type,
                'crypto_amount': t.crypto_amount,
                'crypto_symbol': t.crypto_symbol,
                'fiat_amount': t.fiat_amount,
                'network': t.network,
                'wallet_address': t.wallet_address,
                'crypto_tx_hash': t.crypto_tx_hash,
                'status': t.status,
                'created_at': t.created_at.isoformat(),
            }
            for t in qs
        ]
        
        return Response({
            'success': True, 
            'transactions': data,
            'debug': {
                'vendor_id': v.id,
                'vendor_email': v.email,
                'trans_by_vendor': by_vendor,
                'trans_by_email': by_email,
                'total_in_db': all_trans
            }
        })

class VendorStatsView(APIView):
    def get(self, request):
        v = get_vendor(request)
        if not v:
            return Response({'detail':'unauthorized'}, status=401)
        from django.db.models import Q
        total = Transaction.objects.filter(Q(vendor=v) | Q(customer_email=v.email)).count()
        completed = Transaction.objects.filter(Q(vendor=v) | Q(customer_email=v.email), status='completed').count()
        vol = Transaction.objects.filter(Q(vendor=v) | Q(customer_email=v.email), status='completed').aggregate(s=Sum('fiat_amount'))['s'] or 0.0
        
        # Calculate total crypto bought (completed buy transactions)
        total_bought = Transaction.objects.filter(
            Q(vendor=v) | Q(customer_email=v.email), 
            type='buy', 
            status='completed'
        ).aggregate(s=Sum('crypto_amount'))['s'] or 0.0
        
        # Calculate total crypto sold (completed sell transactions)
        total_sold = Transaction.objects.filter(
            Q(vendor=v) | Q(customer_email=v.email), 
            type='sell', 
            status='completed'
        ).aggregate(s=Sum('crypto_amount'))['s'] or 0.0
        
        return Response({
            'success': True, 
            'total': total, 
            'completed': completed, 
            'volume_ghs': vol,
            'total_bought_usdt': total_bought,
            'total_sold_usdt': total_sold
        })