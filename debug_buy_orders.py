import os
import django
import sys
from django.conf import settings

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cvp_django.settings')
django.setup()

from api.admin_views import AdminBuyOrdersView
from rest_framework.test import APIRequestFactory, force_authenticate
from api.models import AdminUser

def test_view_execution():
    print("Testing AdminBuyOrdersView execution...")
    factory = APIRequestFactory()
    view = AdminBuyOrdersView.as_view()
    
    # Create a request
    request = factory.get('/api/admin/buy-orders')
    
    # We need to mock authentication/permissions if the decorator enforces it
    # But for now, let's try to call the view method directly if possible, 
    # or use force_authenticate if we have a user.
    # Since we don't have an admin user easily, we might hit permission errors.
    # However, let's see if we can just bypass the decorator or if the error happens before that.
    
    # Actually, let's try to call the 'get' method directly on an instance, bypassing decorators
    # This checks the logic inside the method.
    
    view_instance = AdminBuyOrdersView()
    request.GET = {} # Mock GET params
    
    try:
        response = view_instance.get(request)
        print("View execution successful!")
        print(f"Status Code: {response.status_code}")
        print(f"Data keys: {response.data.keys()}")
        print(f"Total orders: {response.data.get('total')}")
    except Exception as e:
        print(f"VIEW EXECUTION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_view_execution()
