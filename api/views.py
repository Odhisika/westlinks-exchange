import os
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AdminSettings, Asset

BASE = getattr(settings, 'FASTAPI_BASE_URL', os.environ.get('FASTAPI_BASE_URL', 'http://localhost:8000'))

class PublicSettingsView(APIView):
    def get(self, request):
        obj = AdminSettings.objects.order_by('-last_updated').first()
        if obj:
            payload = {
                'buy_rate': float(obj.buy_rate) if obj.buy_rate is not None else None,
                'sell_rate': float(obj.sell_rate) if obj.sell_rate is not None else None,
                'usdt_wallet_address': obj.usdt_wallet_address,
                'last_updated': obj.last_updated.isoformat(),
            }
        else:
            payload = {
                'buy_rate': None,
                'sell_rate': None,
                'usdt_wallet_address': '',
                'last_updated': None,
            }
        return Response({'success': True, 'settings': payload})

class PublicAssetsView(APIView):
    def get(self, request):
        qs = Asset.objects.all()
        items = [
            {
                'id': a.id,
                'symbol': a.symbol,
                'asset_name': a.asset_name,
                'network': a.network,
                'wallet_address': a.wallet_address,
                'memo': a.memo,
                
                # Buy fields
                'buy_rate': float(a.buy_rate) if a.buy_rate is not None else None,
                'buy_fee_percent': float(a.buy_fee_percent),
                'network_fee_usd': float(a.network_fee_usd),
                'min_buy_amount_usd': float(a.min_buy_amount_usd),
                'buy_enabled': a.buy_enabled,
                
                # Sell fields
                'sell_rate': float(a.sell_rate) if a.sell_rate is not None else None,
                'sell_enabled': a.sell_enabled,
                
                'last_updated': a.last_updated.isoformat(),
            }
            for a in qs
        ]
        return Response({'success': True, 'assets': items})