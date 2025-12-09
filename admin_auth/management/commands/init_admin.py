from django.core.management.base import BaseCommand
from admin_auth.models import AdminUser
import secrets

class Command(BaseCommand):
    help = 'Create initial super admin user if none exists'

    def handle(self, *args, **kwargs):
        existing = AdminUser.objects.filter(role='super_admin').first()
        if existing:
            self.stdout.write(self.style.WARNING('Super admin already exists.'))
            self.stdout.write(f"Username: {existing.username} Email: {existing.email}")
            return
        pwd = secrets.token_urlsafe(16)
        admin = AdminUser(username='admin', email='admin@coinvibe.com', full_name='CoinVibe Super Administrator', role='super_admin')
        admin.set_password(pwd)
        admin.save()
        self.stdout.write(self.style.SUCCESS('Super admin created successfully!'))
        self.stdout.write('Username: admin')
        self.stdout.write('Email: admin@coinvibe.com')
        self.stdout.write(f'Password: {pwd}')
        self.stdout.write('IMPORTANT: Save this password securely.')