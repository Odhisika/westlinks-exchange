from django.utils import timezone
from django.db import models
from .models import AdminUser

ROLE_PERMISSIONS = {
    'super_admin': ['manage_admin_users','view_dashboard','manage_settings','manage_assets'],
    'admin': ['view_dashboard','manage_settings','manage_assets'],
    'moderator': ['view_dashboard','manage_assets'],
    'viewer': ['view_dashboard'],
}

def get_current_admin(request):
    token = request.headers.get('Authorization') or ''
    token = token.replace('Bearer ','')
    if not token:
        return None
    admin = AdminUser.objects.filter(session_token=token).first()
    if not admin or not admin.session_expires_at or timezone.now() > admin.session_expires_at:
        return None
    return admin

def require_permission(perm):
    def decorator(view_func):
        def _wrapped(view, request, *args, **kwargs):
            admin = get_current_admin(request)
            if not admin:
                from rest_framework.response import Response
                return Response({'detail':'unauthorized'}, status=401)
            perms = ROLE_PERMISSIONS.get(admin.role, [])
            if perm not in perms:
                from rest_framework.response import Response
                return Response({'detail':'forbidden'}, status=403)
            request.admin = admin
            return view_func(view, request, *args, **kwargs)
        return _wrapped
    return decorator