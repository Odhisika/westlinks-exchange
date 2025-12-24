from django.urls import path, include
from .views import PublicSettingsView, PublicAssetsView

urlpatterns = [
    path('settings', PublicSettingsView.as_view()),
    path('assets', PublicAssetsView.as_view()),
    path('payment-methods/', include('api.payment_methods_urls')),
]