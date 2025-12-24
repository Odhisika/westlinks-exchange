"""
Payment Methods API Views
Handles CRUD operations for user payment methods with email verification
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import random
import string

from .models import Vendor, PaymentMethod, EmailVerification
from .email_service import send_verification_email


class InitiatePaymentMethodView(APIView):
    """Send verification code to add/update payment method"""
    
    def post(self, request):
        # Get token from header  
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return Response({'success': False, 'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get vendor from token
        try:
            from .models import VendorSession
            session = VendorSession.objects.filter(session_token=token).first()
            if not session or session.expires_at < timezone.now():
                return Response({'success': False, 'detail': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)
            
            vendor = session.vendor
        except Exception as e:
            return Response({'success': False, 'detail': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Extract payment method data
        data = request.data
        payment_type = data.get('payment_type')
        
        if payment_type not in ['bank', 'mobilemoney']:
            return Response({'success': False, 'detail': 'Invalid payment type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate required fields based on payment type
        if payment_type == 'mobilemoney':
            if not data.get('mobile_network') or not data.get('mobile_number'):
                return Response({'success': False, 'detail': 'Mobile network and number required'}, status=status.HTTP_400_BAD_REQUEST)
        elif payment_type == 'bank':
            if not data.get('bank_name') or not data.get('account_number') or not data.get('account_name'):
                return Response({'success': False, 'detail': 'Bank details required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate 6-digit code
        code = ''.join(random.choices(string.digits, k=6))
        
        # Create verification record
        verification = EmailVerification.objects.create(
            vendor=vendor,
            code=code,
            purpose='payment_method',
            metadata=data,  # Store the payment method data
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # Send verification email
        email_sent = send_verification_email(
            recipient_email=vendor.email,
            code=code,
            vendor_name=vendor.name
        )
        
        if not email_sent:
            return Response({
                'success': False,
                'detail': 'Failed to send verification email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'verification_id': verification.id,
            'message': f'Verification code sent to {vendor.email}',
            'expires_in_minutes': 10
        })


class VerifyPaymentMethodView(APIView):
    """Verify code and save payment method"""
    
    def post(self, request):
        # Get token from header
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return Response({'success': False, 'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get vendor from token
        try:
            from .models import VendorSession
            session = VendorSession.objects.filter(session_token=token).first()
            if not session or session.expires_at < timezone.now():
                return Response({'success': False, 'detail': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)
            
            vendor = session.vendor
        except Exception as e:
            return Response({'success': False, 'detail': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get verification data
        verification_id = request.data.get('verification_id')
        code = request.data.get('code')
        
        if not verification_id or not code:
            return Response({'success': False, 'detail': 'Verification ID and code required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get verification record
        try:
            verification = EmailVerification.objects.get(id=verification_id, vendor=vendor)
        except EmailVerification.DoesNotExist:
            return Response({'success': False, 'detail': 'Invalid verification ID'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if valid
        if not verification.is_valid():
            return Response({'success': False, 'detail': 'Verification code expired or already used'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check code
        if verification.code != code:
            return Response({'success': False, 'detail': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark as used
        verification.is_used = True
        verification.save()
        
        # Create payment method from metadata
        payment_data = verification.metadata
        payment_method = PaymentMethod.objects.create(
            vendor=vendor,
            payment_type=payment_data.get('payment_type'),
            mobile_network=payment_data.get('mobile_network'),
            mobile_number=payment_data.get('mobile_number'),
            bank_name=payment_data.get('bank_name'),
            account_number=payment_data.get('account_number'),
            account_name=payment_data.get('account_name'),
            nickname=payment_data.get('nickname'),
            is_default=payment_data.get('is_default', False),
            is_verified=True
        )
        
        return Response({
            'success': True,
            'message': 'Payment method added successfully',
            'payment_method': {
                'id': payment_method.id,
                'payment_type': payment_method.payment_type,
                'mobile_network': payment_method.mobile_network,
                'mobile_number': payment_method.mobile_number,
                'bank_name': payment_method.bank_name,
                'account_number': payment_method.account_number,
                'account_name': payment_method.account_name,
                'nickname': payment_method.nickname,
                'is_default': payment_method.is_default,
                'is_verified': payment_method.is_verified,
                'created_at': payment_method.created_at.isoformat(),
            }
        })


class ListPaymentMethodsView(APIView):
    """List all payment methods for authenticated user"""
    
    def get(self, request):
        # Get token from header
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return Response({'success': False, 'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get vendor from token
        try:
            from .models import VendorSession
            session = VendorSession.objects.filter(session_token=token).first()
            if not session or session.expires_at < timezone.now():
                return Response({'success': False, 'detail': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)
            
            vendor = session.vendor
        except Exception as e:
            return Response({'success': False, 'detail': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get all payment methods for this vendor
        payment_methods = PaymentMethod.objects.filter(vendor=vendor)
        
        methods_list = [{
            'id': pm.id,
            'payment_type': pm.payment_type,
            'mobile_network': pm.mobile_network,
            'mobile_number': pm.mobile_number,
            'bank_name': pm.bank_name,
            'account_number': pm.account_number,
            'account_name': pm.account_name,
            'nickname': pm.nickname,
            'is_default': pm.is_default,
            'is_verified': pm.is_verified,
            'created_at': pm.created_at.isoformat(),
        } for pm in payment_methods]
        
        return Response({
            'success': True,
            'payment_methods': methods_list
        })


class SetDefaultPaymentMethodView(APIView):
    """Set a payment method as default"""
    
    def put(self, request, payment_method_id):
        # Get token from header
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return Response({'success': False, 'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get vendor from token
        try:
            from .models import VendorSession
            session = VendorSession.objects.filter(session_token=token).first()
            if not session or session.expires_at < timezone.now():
                return Response({'success': False, 'detail': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)
            
            vendor = session.vendor
        except Exception as e:
            return Response({'success': False, 'detail': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get payment method
        try:
            payment_method = PaymentMethod.objects.get(id=payment_method_id, vendor=vendor)
        except PaymentMethod.DoesNotExist:
            return Response({'success': False, 'detail': 'Payment method not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Set as default (model's save method will handle unsetting others)
        payment_method.is_default = True
        payment_method.save()
        
        return Response({
            'success': True,
            'message': 'Default payment method updated'
        })


class DeletePaymentMethodView(APIView):
    """Delete a payment method"""
    
    def delete(self, request, payment_method_id):
        # Get token from header
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return Response({'success': False, 'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get vendor from token
        try:
            from .models import VendorSession
            session = VendorSession.objects.filter(session_token=token).first()
            if not session or session.expires_at < timezone.now():
                return Response({'success': False, 'detail': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)
            
            vendor = session.vendor
        except Exception as e:
            return Response({'success': False, 'detail': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get payment method
        try:
            payment_method = PaymentMethod.objects.get(id=payment_method_id, vendor=vendor)
        except PaymentMethod.DoesNotExist:
            return Response({'success': False, 'detail': 'Payment method not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete
        payment_method.delete()
        
        return Response({
            'success': True,
            'message': 'Payment method deleted successfully'
        })
