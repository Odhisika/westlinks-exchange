import requests
from django.conf import settings

BASE = getattr(settings, 'PAYSTACK_BASE_URL', 'https://api.paystack.co')
KEY = getattr(settings, 'PAYSTACK_SECRET_KEY', '')

def _headers():
    return {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}

def create_recipient(name, email, momo_number):
    data = {'type': 'mobile_money', 'name': name, 'email': email, 'mobile_money': {'phone': momo_number, 'provider': 'mtn'}}
    r = requests.post(f'{BASE}/transferrecipient', json=data, headers=_headers(), timeout=10)
    return r.status_code, r.json()

def initiate_transfer(amount_ghs, recipient_code, reason):
    data = {'source': 'balance', 'amount': int(round(amount_ghs * 100)), 'recipient': recipient_code, 'reason': reason, 'currency': 'GHS'}
    r = requests.post(f'{BASE}/transfer', json=data, headers=_headers(), timeout=10)
    return r.status_code, r.json()

def verify_transfer(reference):
    r = requests.get(f'{BASE}/transfer/verify/{reference}', headers=_headers(), timeout=10)
    return r.status_code, r.json()