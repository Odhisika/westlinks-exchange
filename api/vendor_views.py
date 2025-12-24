from django.utils import timezone
from django.db.models import Q, Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password, check_password
from .models import Vendor, VendorSession, Transaction, BuyOrder
from .email_service import send_welcome_email
import secrets
import re
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

def validate_password_strength(password, username='', email=''):
    """
    Validate password strength with multiple security checks
    Returns: (is_valid: bool, error_message: str)
    """
    # Common weak passwords blacklist
    common_passwords = [
        '123456', 'password', '12345678', 'qwerty', '123456789', '12345',
        '1234', '111111', '1234567', 'dragon', '123123', 'baseball', 'iloveyou',
        'trustno1', '1234567890', 'sunshine', 'master', 'welcome', 'shadow',
        'ashley', 'football', 'jesus', 'michael', 'ninja', 'mustang', 'password1'
    ]
    
    # Check minimum length
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    
    # Check for uppercase
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    
    # Check for lowercase
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    
    # Check for number
    if not re.search(r'[0-9]', password):
        return False, 'Password must contain at least one number'
    
    # Check against common passwords
    if password.lower() in common_passwords:
        return False, 'This password is too common. Please choose a stronger password'
    
    # Check similarity to username
    if username and len(username) > 2:
        username_lower = username.lower()
        password_lower = password.lower()
        if username_lower in password_lower or password_lower in username_lower:
            return False, 'Password cannot be similar to your name'
    
    # Check similarity to email
    if email and len(email) > 2:
        email_parts = email.lower().split('@')[0]
        password_lower = password.lower()
        if email_parts in password_lower or password_lower in email_parts:
            return False, 'Password cannot be similar to your email'
    
    return True, ''


@method_decorator(csrf_exempt, name='dispatch')
class VendorRegisterView(APIView):
    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')
        password_confirmation = request.data.get('password_confirmation')
        momo = request.data.get('momo_number')
        
        # Check all required fields
        if not all([name, email, password, momo]):
            return Response({'detail':'missing_fields', 'success': False}, status=400)
        
        # Check password confirmation
        if not password_confirmation:
            return Response({'detail':'password_confirmation_required', 'success': False}, status=400)
        
        if password != password_confirmation:
            return Response({'detail':'passwords_do_not_match', 'success': False}, status=400)
        
        # Validate password strength
        is_valid, error_message = validate_password_strength(password, username=name, email=email)
        if not is_valid:
            return Response({'detail': error_message, 'success': False}, status=400)
        
        # Check if email already exists
        if Vendor.objects.filter(email=email).exists():
            return Response({'detail':'email_exists', 'success': False}, status=400)
        
        # Create vendor
        v = Vendor(name=name, email=email, password_hash=make_password(password), momo_number=momo)
        v.save()
        
        # Send welcome email
        email_sent = send_welcome_email(v.email, v.name)
        if not email_sent:
            print(f"WARNING: Failed to send welcome email to {v.email}")
        
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
        
        # Fetch BuyOrder statuses
        buy_payment_ids = [t.payment_id for t in qs if t.type == 'buy']
        buy_orders = {b.order_id: {'delivery': b.delivery_status, 'payment': b.payment_status} for b in BuyOrder.objects.filter(order_id__in=buy_payment_ids)}
        
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
                'delivery_status': buy_orders.get(t.payment_id, {}).get('delivery') if t.type == 'buy' else None,
                'payment_status': buy_orders.get(t.payment_id, {}).get('payment') if t.type == 'buy' else None,
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

class VendorTransactionDetailView(APIView):
    def get(self, request, payment_id):
        v = get_vendor(request)
        if not v:
            return Response({'detail':'unauthorized'}, status=401)
        
        t = Transaction.objects.filter(payment_id=payment_id).filter(Q(vendor=v) | Q(customer_email=v.email)).first()
        
        if not t:
            return Response({'detail':'not_found'}, status=404)
            
        delivery_status = None
        payment_status = None
        if t.type == 'buy':
            b = BuyOrder.objects.filter(order_id=t.payment_id).first()
            if b:
                delivery_status = b.delivery_status
                payment_status = b.payment_status
        
        data = {
            'payment_id': t.payment_id,
            'type': t.type,
            'crypto_amount': t.crypto_amount,
            'crypto_symbol': t.crypto_symbol,
            'fiat_amount': t.fiat_amount,
            'exchange_rate': t.exchange_rate,
            'coinvibe_fee': t.coinvibe_fee,
            'network_fee': t.network_fee,
            'network': t.network,
            'wallet_address': t.wallet_address,
            'crypto_tx_hash': t.crypto_tx_hash,
            'status': t.status,
            'delivery_status': delivery_status,
            'payment_status': payment_status,
            'created_at': t.created_at.isoformat(),
        }
        
        return Response({'success': True, 'transaction': data})

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