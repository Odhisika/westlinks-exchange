from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from web import views

def health(_):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')),
    path('', include('web.urls')),
    path('api/public/', include('api.urls')),
    path('api/admin/auth/', include('admin_auth.urls')),
    path('api/admin/', include('api.admin_urls')),
    path('api/', include('api.vendor_urls')),
    path('learn/', include('learn_crypto.urls')),
    path('api/', include('api.transaction_urls')),
    path('api/', include('api.payment_urls')),
    path('api/', include('api.payout_urls')),
    path('api/payment-methods/', include('api.payment_methods_urls')),
    path('api/exchange/', include('api.exchange_urls')),
    path('health', health),
    path('password-reset/', views.VendorPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.VendorPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.VendorPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.VendorPasswordResetCompleteView.as_view(), name='password_reset_complete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)