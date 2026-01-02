from datetime import datetime
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from .models import User, Crop, Market, MarketPrice, AlertSubscription, AlertHistory
from rest_framework_simplejwt.tokens import RefreshToken

class GovMarketPricesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client = Client()
        
        # Authenticate via cookie
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['access'] = str(refresh.access_token)
        
        self.crop = Crop.objects.create(name="wheat")
        self.market = Market.objects.create(name="test market", state="Test State", district="Test District")
        self.alert = AlertSubscription.objects.create(
            user=self.user,
            crop=self.crop,
            market=self.market,
            target_min=100,
            target_max=5000,
            status="active"
        )

    @patch('requests.get')
    def test_gov_market_prices_success(self, mock_get):
        # Mocking Gov API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "records": [
                {
                    "state": "Test State",
                    "district": "Test District",
                    "market": "test market",
                    "commodity": "wheat",
                    "arrival_date": "02/01/2026",
                    "min_price": "1000",
                    "max_price": "2000",
                    "modal_price": "1500"
                },
                {
                    "state": "Test State",
                    "district": "Test District",
                    "market": "invalid date market",
                    "commodity": "wheat",
                    "arrival_date": "invalid",
                    "min_price": "1000",
                    "max_price": "2000",
                    "modal_price": "1500"
                }
            ]
        }

        url = reverse('gov_market_prices')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['prices']), 1) # Only one record has a valid date
        
        # Check if alert was triggered and history created
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, "triggered")
        self.assertTrue(AlertHistory.objects.filter(subscription=self.alert).exists())
        self.assertIn("Market Alert", AlertHistory.objects.first().message)

    @patch('requests.get')
    def test_gov_market_prices_fallback(self, mock_get):
        # Create some local data for fallback
        MarketPrice.objects.create(
            crop=self.crop,
            market=self.market,
            arrival_date=datetime.now().date(),
            min_price=1200,
            max_price=2200,
            modal_price=1700
        )

        # Mock Gov API failure
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = '{"error": "Internal Server Error"}'

        url = reverse('gov_market_prices')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['prices']), 1)
        self.assertEqual(response.json()['prices'][0]['source'], "local_cache")
        self.assertIn("warning", response.json())
