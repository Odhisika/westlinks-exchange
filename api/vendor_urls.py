from django.urls import path
from .vendor_views import (
    VendorRegisterView,
    VendorLoginView,
    VendorMeView,
    VendorPasswordView,
    VendorTransactionsView,
    VendorStatsView,
)

urlpatterns = [
    path('vendors/register', VendorRegisterView.as_view()),
    path('vendors/login', VendorLoginView.as_view()),
    path('vendors/me', VendorMeView.as_view()),
    path('vendors/me/password', VendorPasswordView.as_view()),
    path('vendors/me/transactions', VendorTransactionsView.as_view()),
    path('vendors/me/stats', VendorStatsView.as_view()),
]