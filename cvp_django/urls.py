from django.urls import path, include
from django.http import JsonResponse

def health(_):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('', include('web.urls')),
    path('api/public/', include('api.urls')),
    path('api/admin/auth/', include('admin_auth.urls')),
    path('api/admin/', include('api.admin_urls')),
    path('api/', include('api.vendor_urls')),
    path('api/', include('api.transaction_urls')),
    path('api/', include('api.payment_urls')),
    path('api/', include('api.payout_urls')),
    path('api/exchange/', include('api.exchange_urls')),
    path('health', health),
]