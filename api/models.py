from django.db import models
from django.utils import timezone

class AdminSettings(models.Model):
    buy_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sell_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    usdt_wallet_address = models.CharField(max_length=128, blank=True)
    last_updated = models.DateTimeField(default=timezone.now)

class Asset(models.Model):
    symbol = models.CharField(max_length=16)
    asset_name = models.CharField(max_length=64)
    network = models.CharField(max_length=32)
    wallet_address = models.CharField(max_length=256, blank=True)
    memo = models.CharField(max_length=256, blank=True)
    
    # Buy-specific fields
    buy_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Buy rate in GHS per unit")
    buy_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=1.50, help_text="Service fee percentage")
    network_fee_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0.00, help_text="Fixed network fee in USD")
    min_buy_amount_usd = models.DecimalField(max_digits=10, decimal_places=2, default=10.00, help_text="Minimum buy amount in USD")
    buy_enabled = models.BooleanField(default=True, help_text="Enable/disable buying for this asset")
    
    # Sell-specific fields
    sell_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sell_enabled = models.BooleanField(default=True)
    
    last_updated = models.DateTimeField(default=timezone.now)

class Vendor(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    momo_number = models.CharField(max_length=50)
    country = models.CharField(max_length=2, default='GH')
    balance = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    paystack_recipient_code = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

class Wallet(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='wallets')
    address = models.CharField(max_length=255, unique=True)
    network = models.CharField(max_length=20)
    crypto_symbol = models.CharField(max_length=10, default='USDT')
    is_active = models.BooleanField(default=True)
    is_monitored = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_used = models.DateTimeField(blank=True, null=True)

class Transaction(models.Model):
    payment_id = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10, default='buy')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='transactions')
    wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, blank=True, null=True, related_name='transactions')
    crypto_amount = models.FloatField()
    crypto_symbol = models.CharField(max_length=10, default='USDT')
    network = models.CharField(max_length=20)
    tx_hash = models.CharField(max_length=255, blank=True, null=True)
    wallet_address = models.CharField(max_length=255)
    crypto_address_used = models.CharField(max_length=255, blank=True, null=True)
    crypto_tx_hash = models.CharField(max_length=255, blank=True, null=True)
    fiat_amount = models.FloatField(blank=True, null=True)
    fiat_currency = models.CharField(max_length=3, default='GHS')
    exchange_rate = models.FloatField(blank=True, null=True)
    rate_used = models.FloatField(blank=True, null=True)
    coinvibe_fee = models.FloatField(default=0.0)
    network_fee = models.FloatField(default=0.0)
    vendor_receives = models.FloatField(blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    payout_reference = models.CharField(max_length=100, blank=True, null=True)
    payout_status = models.CharField(max_length=20, blank=True, null=True)
    transfer_code = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    detected_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    blockchain_confirmations = models.IntegerField(default=0)
    last_chain_check = models.DateTimeField(blank=True, null=True)
    chain_metadata = models.JSONField(default=dict, blank=True)

class BuyOrder(models.Model):
    order_id = models.CharField(max_length=100, unique=True)
    
    # Asset & Amount
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True)  # NEW
    asset_symbol = models.CharField(max_length=16, default='USDT')  # NEW - fallback
    amount_ghs = models.FloatField()
    rate_usd_to_ghs = models.FloatField()
    usdt_amount = models.FloatField()  # Rename to crypto_amount later
    fee_percent = models.FloatField(default=0.0)
    fee_ghs = models.FloatField(default=0.0)
    network_fee_ghs = models.FloatField(default=0.0)  # NEW
    total_charge_ghs = models.FloatField()
    
    # Network & Delivery
    network = models.CharField(max_length=20)
    recipient_address = models.CharField(max_length=255)
    tx_hash = models.CharField(max_length=255, blank=True, null=True)
    
    # Status Tracking
    status = models.CharField(max_length=20, default='pending')  # Overall status
    payment_status = models.CharField(max_length=20, default='pending')  # NEW: pending, paid, failed
    delivery_status = models.CharField(max_length=20, default='pending')  # NEW: pending, sent, confirmed
    
    # Payment Details
    paystack_reference = models.CharField(max_length=255, blank=True, null=True)  # NEW
    payment_reference = models.CharField(max_length=255, blank=True, null=True)   # NEW - For manual payments
    momo_number = models.CharField(max_length=50, blank=True, null=True)
    momo_provider = models.CharField(max_length=50, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    paid_at = models.DateTimeField(blank=True, null=True)  # NEW
    delivered_at = models.DateTimeField(blank=True, null=True)  # NEW
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Admin Notes
    admin_notes = models.TextField(blank=True, null=True)  # NEW

class AuditLog(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, blank=True, null=True)
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

class VendorSession(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='sessions')
    session_token = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

class ExchangeRate(models.Model):
    """Admin-managed exchange rates for NGN <-> GHS"""
    ngn_to_ghs_rate = models.FloatField(default=0.0043)  # 1 NGN = 0.0043 GHS (approx 230 NGN = 1 GHS)
    ghs_to_ngn_rate = models.FloatField(default=230.0)   # 1 GHS = 230 NGN
    fee_percent = models.FloatField(default=2.0)
    min_exchange_ghs = models.FloatField(default=100.0)
    max_exchange_ghs = models.FloatField(default=10000.0)
    min_exchange_ngn = models.FloatField(default=50000.0)
    max_exchange_ngn = models.FloatField(default=5000000.0)
    last_updated = models.DateTimeField(default=timezone.now)

class ExchangePaymentSettings(models.Model):
    """Admin-configured payment details for currency exchanges"""
    # Nigerian Naira (NGN) - Bank Transfer
    ngn_bank_name = models.CharField(max_length=100, blank=True, default='')
    ngn_account_number = models.CharField(max_length=50, blank=True, default='')
    ngn_account_name = models.CharField(max_length=100, blank=True, default='')
    
    # Ghana Cedis (GHS) - Mobile Money
    ghs_momo_number = models.CharField(max_length=20, blank=True, default='')
    ghs_momo_name = models.CharField(max_length=100, blank=True, default='')
    ghs_momo_network = models.CharField(max_length=20, blank=True, default='MTN')  # MTN, Vodafone, AirtelTigo
    
    # Ghana Cedis (GHS) - Bank Transfer
    ghs_bank_name = models.CharField(max_length=100, blank=True, default='')
    ghs_account_number = models.CharField(max_length=50, blank=True, default='')
    ghs_account_name = models.CharField(max_length=100, blank=True, default='')
    
    last_updated = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Exchange Payment Settings"
        verbose_name_plural = "Exchange Payment Settings"


class CurrencyExchange(models.Model):
    """Currency exchange transactions between NGN and GHS"""
    exchange_id = models.CharField(max_length=100, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='exchanges')
    
    # Exchange details
    from_currency = models.CharField(max_length=3)  # 'NGN' or 'GHS'
    to_currency = models.CharField(max_length=3)    # 'NGN' or 'GHS'
    from_amount = models.FloatField()
    to_amount = models.FloatField()
    exchange_rate = models.FloatField()
    fee_amount = models.FloatField()
    
    # Recipient details (stored as JSON for flexibility)
    recipient_details = models.JSONField(default=dict)  # {phone, bank_account, account_name, etc.}
    
    # Payment tracking
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    
    # Status tracking
    # Flow: pending_payment -> paid -> processing -> completed / failed
    status = models.CharField(max_length=20, default='pending_payment')
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    paid_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Admin notes
    admin_notes = models.TextField(blank=True, null=True)


class PaymentMethod(models.Model):
    """User's saved payment methods for receiving crypto sale proceeds"""
    PAYMENT_TYPE_CHOICES = [
        ('bank', 'Bank Transfer'),
        ('mobilemoney', 'Mobile Money'),
    ]
    
    MOBILE_NETWORK_CHOICES = [
        ('mtn', 'MTN Mobile Money'),
        ('vodafone', 'Vodafone Cash'),
        ('airteltigo', 'AirtelTigo Money'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    
    # Mobile Money fields
    mobile_network = models.CharField(max_length=20, choices=MOBILE_NETWORK_CHOICES, blank=True, null=True)
    mobile_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Bank Transfer fields
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Metadata
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    nickname = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., 'My MTN Account'")
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per vendor
        if self.is_default:
            PaymentMethod.objects.filter(vendor=self.vendor, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class EmailVerification(models.Model):
    """Email verification codes for payment method changes"""
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='email_verifications')
    code = models.CharField(max_length=6)  # 6-digit code
    purpose = models.CharField(max_length=50, default='payment_method')  # Future: password_reset, email_change, etc.
    metadata = models.JSONField(default=dict, blank=True)  # Store pending payment method data
    
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at