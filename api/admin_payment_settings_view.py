from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import ExchangePaymentSettings
from admin_auth.permissions import require_permission


class AdminExchangePaymentSettingsView(APIView):
    """Get and update exchange payment settings"""
    
    @require_permission('view_dashboard')
    def get(self, request):
        settings = ExchangePaymentSettings.objects.order_by('-last_updated').first()
        
        if not settings:
            # Create default settings if none exist
            settings = ExchangePaymentSettings.objects.create()
        
        return Response({
            'success': True,
            'settings': {
                # NGN Settings
                'ngn_bank_name': settings.ngn_bank_name,
                'ngn_account_number': settings.ngn_account_number,
                'ngn_account_name': settings.ngn_account_name,
                
                # GHS Settings
                'ghs_momo_number': settings.ghs_momo_number,
                'ghs_momo_name': settings.ghs_momo_name,
                'ghs_momo_network': settings.ghs_momo_network,
                
                'last_updated': settings.last_updated.isoformat() if settings.last_updated else None
            }
        })
    
    @require_permission('manage_admin_users')
    def put(self, request):
        settings = ExchangePaymentSettings.objects.order_by('-last_updated').first()
        
        if not settings:
            settings = ExchangePaymentSettings.objects.create()
        
        # Update NGN settings
        if 'ngn_bank_name' in request.data:
            settings.ngn_bank_name = request.data['ngn_bank_name']
        if 'ngn_account_number' in request.data:
            settings.ngn_account_number = request.data['ngn_account_number']
        if 'ngn_account_name' in request.data:
            settings.ngn_account_name = request.data['ngn_account_name']
        
        # Update GHS settings
        if 'ghs_momo_number' in request.data:
            settings.ghs_momo_number = request.data['ghs_momo_number']
        if 'ghs_momo_name' in request.data:
            settings.ghs_momo_name = request.data['ghs_momo_name']
        if 'ghs_momo_network' in request.data:
            settings.ghs_momo_network = request.data['ghs_momo_network']
        
        settings.last_updated = timezone.now()
        settings.save()
        
        return Response({
            'success': True,
            'message': 'Payment settings updated successfully'
        })
