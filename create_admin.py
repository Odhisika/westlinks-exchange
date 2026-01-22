import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cvp_django.settings')
django.setup()

from admin_auth.models import AdminUser
from django.contrib.auth.hashers import make_password

def create_admin():
    print("Create New Admin User")
    print("---------------------")
    
    username = input("Username: ").strip()
    if not username:
        print("Error: Username is required")
        return

    if AdminUser.objects.filter(username=username).exists():
        print("Error: Username already exists")
        return

    email = input("Email: ").strip()
    if not email:
        print("Error: Email is required")
        return
        
    if AdminUser.objects.filter(email=email).exists():
        print("Error: Email already exists")
        return

    password = input("Password: ").strip()
    if not password:
        print("Error: Password is required")
        return

    role = input("Role (super_admin/admin/moderator/viewer) [super_admin]: ").strip()
    if not role:
        role = 'super_admin'
    
    if role not in ['super_admin', 'admin', 'moderator', 'viewer']:
        print("Error: Invalid role")
        return

    try:
        admin = AdminUser(
            username=username,
            email=email,
            full_name=username,  # Default full name to username
            role=role,
            password_hash=make_password(password),
            is_active=True,
            is_verified=True
        )
        admin.save()
        print(f"\nSuccess! Admin user '{username}' created with role '{role}'")
        
    except Exception as e:
        print(f"Error creating admin: {str(e)}")

if __name__ == "__main__":
    create_admin()
