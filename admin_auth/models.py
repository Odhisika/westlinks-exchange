from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
import secrets

class AdminUser(models.Model):
    ROLE_CHOICES = (
        ('super_admin','super_admin'),
        ('admin','admin'),
        ('moderator','moderator'),
        ('viewer','viewer'),
    )
    username = models.CharField(max_length=64, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=128, blank=True)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default='viewer')
    password_hash = models.CharField(max_length=256)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=True)
    failed_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    session_token = models.CharField(max_length=128, null=True, blank=True)
    session_expires_at = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.CharField(max_length=128, null=True, blank=True)
    password_reset_expires_at = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    login_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw):
        self.password_hash = make_password(raw)

    def check_password(self, raw):
        return check_password(raw, self.password_hash)

    def generate_session(self, hours=24):
        self.session_token = secrets.token_urlsafe(32)
        self.session_expires_at = timezone.now() + timezone.timedelta(hours=hours)
        self.last_login = timezone.now()
        self.login_count = (self.login_count or 0) + 1

    def clear_session(self):
        self.session_token = None
        self.session_expires_at = None

    def generate_reset_token(self, minutes=30):
        self.password_reset_token = secrets.token_urlsafe(24)
        self.password_reset_expires_at = timezone.now() + timezone.timedelta(minutes=minutes)
        return self.password_reset_token

    def is_reset_token_valid(self, token):
        return token and self.password_reset_token == token and self.password_reset_expires_at and timezone.now() < self.password_reset_expires_at

class AdminSession(models.Model):
    admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='sessions')
    session_token = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=256, blank=True)
    device_info = models.CharField(max_length=256, blank=True)
    invalidated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def invalidate(self, reason=""):
        self.invalidated_at = timezone.now()

class AdminAuditLog(models.Model):
    admin_user = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=64)
    action_description = models.CharField(max_length=256, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=256, blank=True)
    session_token = models.CharField(max_length=128, blank=True)
    risk_level = models.CharField(max_length=32, default='low')
    suspicious = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class AdminPasswordHistory(models.Model):
    admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='password_history')
    password_hash = models.CharField(max_length=256)
    changed_by = models.CharField(max_length=64, blank=True)
    reason = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)