import os
import requests
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AdminUser, AdminSession, AdminAuditLog, AdminPasswordHistory
from .permissions import ROLE_PERMISSIONS, get_current_admin, require_permission
from django.db.models import Q

BASE = getattr(settings, 'FASTAPI_BASE_URL', os.environ.get('FASTAPI_BASE_URL', 'http://localhost:8000'))

def client_info(request):
    return {
        'ip_address': request.META.get('REMOTE_ADDR',''),
        'user_agent': request.META.get('HTTP_USER_AGENT',''),
    }

class AdminLoginView(APIView):
    def post(self, request):
        data = request.data or {}
        u = data.get('username_or_email')
        p = data.get('password')
        if not u or not p:
            return Response({'success': False, 'detail': 'Invalid credentials'}, status=401)
        qs = AdminUser.objects.filter(Q(username=u) | Q(email=u))
        admin = qs.first()
        if not admin or not admin.check_password(p):
            AdminAuditLog.objects.create(action='admin_login_failed', action_description=f'Failed login {u}', **client_info(request))
            return Response({'success': False, 'detail': 'Invalid credentials'}, status=401)
        if admin.locked_until and timezone.now() < admin.locked_until:
            return Response({'success': False, 'detail': 'Account locked'}, status=401)
        admin.generate_session()
        admin.save()
        AdminSession.objects.create(admin_user=admin, session_token=admin.session_token, expires_at=admin.session_expires_at, **client_info(request))
        AdminAuditLog.objects.create(admin_user=admin, action='admin_login_success', action_description='Admin login', session_token=admin.session_token, **client_info(request))
        return Response({
            'success': True,
            'message': 'Login successful',
            'session_token': admin.session_token,
            'admin_user': {
                'id': admin.id,
                'username': admin.username,
                'email': admin.email,
                'full_name': admin.full_name,
                'role': admin.role,
            },
            'expires_at': admin.session_expires_at.isoformat() if admin.session_expires_at else None
        })

class AdminLogoutView(APIView):
    def post(self, request):
        token = request.headers.get('Authorization')
        if not token:
            return Response({'success': False, 'message': 'missing_token'}, status=401)
        admin = AdminUser.objects.filter(session_token=token.replace('Bearer ','')).first()
        if not admin:
            return Response({'success': False, 'message': 'invalid_token'}, status=401)
        sess = AdminSession.objects.filter(session_token=admin.session_token).first()
        if sess:
            sess.invalidate('User logged out')
            sess.save()
        admin.clear_session()
        admin.save()
        AdminAuditLog.objects.create(admin_user=admin, action='admin_logout', action_description='Admin logout', **client_info(request))
        return Response({'success': True, 'message': 'Logout successful'})

class SessionStatusView(APIView):
    def get(self, request):
        token = request.headers.get('Authorization')
        if not token:
            return Response({'valid': False}, status=401)
        t = token.replace('Bearer ','')
        admin = AdminUser.objects.filter(session_token=t).first()
        if not admin or not admin.session_expires_at or timezone.now() > admin.session_expires_at:
            return Response({'valid': False}, status=401)
        return Response({'valid': True, 'admin': {'id': admin.id, 'username': admin.username, 'role': admin.role}, 'expires_at': admin.session_expires_at.isoformat()})

class AdminProfileView(APIView):
    def get(self, request):
        admin = get_current_admin(request)
        if not admin:
            return Response({'detail':'unauthorized'}, status=401)
        return Response({
            'id': admin.id,
            'username': admin.username,
            'email': admin.email,
            'full_name': admin.full_name,
            'role': admin.role,
            'is_active': admin.is_active,
            'is_verified': admin.is_verified,
            'last_login': admin.last_login.isoformat() if admin.last_login else None,
            'login_count': admin.login_count,
            'created_at': admin.created_at.isoformat(),
        })

class ChangePasswordView(APIView):
    def post(self, request):
        admin = get_current_admin(request)
        if not admin:
            return Response({'detail':'unauthorized'}, status=401)
        cur = request.data.get('current_password')
        new = request.data.get('new_password')
        if not admin.check_password(cur):
            AdminAuditLog.objects.create(admin_user=admin, action='password_change_failed', action_description='Incorrect current password', suspicious=True, **client_info(request))
            return Response({'detail':'Current password is incorrect'}, status=400)
        AdminPasswordHistory.objects.create(admin_user=admin, password_hash=admin.password_hash, changed_by=admin.username, reason='manual_change')
        admin.set_password(new)
        admin.save()
        AdminAuditLog.objects.create(admin_user=admin, action='password_changed', action_description='Password changed', **client_info(request))
        return Response({'success': True, 'message': 'Password changed successfully'})

class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        admin = AdminUser.objects.filter(email=email).first()
        if not admin:
            return Response({'success': True, 'message': 'If the email exists, a reset link has been sent'})
        token = admin.generate_reset_token()
        admin.save()
        AdminAuditLog.objects.create(admin_user=admin, action='password_reset_requested', action_description='Password reset requested', **client_info(request))
        return Response({'success': True, 'message': 'If the email exists, a reset link has been sent', 'reset_token': token})

class ResetPasswordView(APIView):
    def post(self, request):
        token = request.data.get('token')
        new = request.data.get('new_password')
        admin = AdminUser.objects.filter(password_reset_token=token).first()
        if not admin or not admin.is_reset_token_valid(token):
            return Response({'detail':'Invalid or expired reset token'}, status=400)
        AdminPasswordHistory.objects.create(admin_user=admin, password_hash=admin.password_hash, changed_by='system', reason='password_reset')
        admin.set_password(new)
        admin.password_reset_token = None
        admin.password_reset_expires_at = None
        admin.save()
        AdminAuditLog.objects.create(admin_user=admin, action='password_reset_completed', action_description='Password reset completed', **client_info(request))
        return Response({'success': True, 'message': 'Password reset successful'})

class CreateAdminView(APIView):
    @require_permission('manage_admin_users')
    def post(self, request):
        creator = request.admin
        role = request.data.get('role')
        if role not in ROLE_PERMISSIONS:
            return Response({'detail': f'Invalid role. Must be one of: {list(ROLE_PERMISSIONS.keys())}'}, status=400)
        admin = AdminUser(
            username=request.data.get('username'),
            email=request.data.get('email'),
            full_name=request.data.get('full_name',''),
            role=role,
        )
        admin.set_password(request.data.get('password'))
        admin.save()
        AdminAuditLog.objects.create(admin_user=creator, action='admin_user_created', action_description=f'Created {admin.username} ({admin.role})', **client_info(request))
        return Response({
            'id': admin.id,
            'username': admin.username,
            'email': admin.email,
            'full_name': admin.full_name,
            'role': admin.role,
        })

class ListAdminsView(APIView):
    @require_permission('manage_admin_users')
    def get(self, request):
        admins = AdminUser.objects.exclude(id=request.admin.id)
        return Response([
            {
                'id': a.id,
                'username': a.username,
                'email': a.email,
                'full_name': a.full_name,
                'role': a.role,
                'is_active': a.is_active,
            }
            for a in admins
        ])