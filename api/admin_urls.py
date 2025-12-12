from django.urls import path
from .admin_views import (
    AdminSettingsUpdateView,
    AdminAssetsListView,
    AdminAssetUpdateView,
    AdminOverviewView,
    AdminVendorsView,
    AdminVendorUpdateView,
    AdminTransactionsView,
    AdminBuyOrdersView,
    AdminBuyOrderUpdateView,
    AdminAuditLogsView,
    AdminExchangeRatesView,
    AdminExchangesView,
    AdminExchangeUpdateView,
    AdminSellOrdersView,
    AdminSellOrderUpdateView,
)
from .admin_payment_settings_view import AdminExchangePaymentSettingsView

urlpatterns = [
    path('settings', AdminSettingsUpdateView.as_view()),
    path('assets', AdminAssetsListView.as_view()),
    path('assets/<int:asset_id>', AdminAssetUpdateView.as_view()),
    path('overview', AdminOverviewView.as_view()),
    path('vendors', AdminVendorsView.as_view()),
    path('vendors/<int:vendor_id>', AdminVendorUpdateView.as_view()),
    path('transactions', AdminTransactionsView.as_view()),
    path('buy-orders', AdminBuyOrdersView.as_view()),
    path('buy-orders/<int:order_id>', AdminBuyOrderUpdateView.as_view()),
    path('audit-logs', AdminAuditLogsView.as_view()),
    path('exchange-rates', AdminExchangeRatesView.as_view()),
    path('exchange-payment-settings', AdminExchangePaymentSettingsView.as_view()),
    path('exchanges', AdminExchangesView.as_view()),
    path('exchanges/<str:exchange_id>', AdminExchangeUpdateView.as_view()),
    path('sell-orders', AdminSellOrdersView.as_view()),
    path('sell-orders/<str:payment_id>', AdminSellOrderUpdateView.as_view()),
]