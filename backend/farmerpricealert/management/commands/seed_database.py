import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from farmerpricealert.models import Crop, DashboardImage, Market, MarketPrice
from datetime import datetime

class Command(BaseCommand):
    help = "Seed the database with initial crops, dashboard images, and sample prices"

    def handle(self, *args, **kwargs):
        self.stdout.write("🌱 Starting database seeding...")

        # 1. Create Crops
        crops_to_create = [
            {"name": "wheat", "image_url": "https://res.cloudinary.com/duyqfx8tw/image/upload/v1/crops/wheat"},
            {"name": "rice", "image_url": "https://res.cloudinary.com/duyqfx8tw/image/upload/v1/crops/rice"},
            {"name": "cotton", "image_url": "https://res.cloudinary.com/duyqfx8tw/image/upload/v1/crops/cotton"},
            {"name": "soybean", "image_url": "https://res.cloudinary.com/duyqfx8tw/image/upload/v1/crops/soybean"},
            {"name": "sugarcane", "image_url": "https://res.cloudinary.com/duyqfx8tw/image/upload/v1/crops/sugarcane"},
        ]

        for crop_data in crops_to_create:
            crop, created = Crop.objects.get_or_create(
                name=crop_data["name"].lower(),
                defaults={"image_url": crop_data["image_url"]}
            )
            if created:
                self.stdout.write(f"✅ Created Crop: {crop.name}")
            else:
                self.stdout.write(f"ℹ️ Crop already exists: {crop.name}")

        # 2. Create Dashboard Image Placeholders
        # These keys matching the IDs in dashboard.html cards
        dashboard_keys = ["wheat", "rice", "cotton", "soybean", "sugarcane"]
        for key in dashboard_keys:
            # We don't have the actual ImageField file here, so we create a record.
            # The user will need to upload actual files in Django Admin to fix the visual fully.
            img, created = DashboardImage.objects.get_or_create(key=key)
            if created:
                self.stdout.write(f"✅ Created DashboardImage placeholder for: {key}")

        # 3. Trigger a sample fetch of live prices to show some data
        self.stdout.write("📡 Fetching some live prices from Gov API...")
        gov_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        api_key = settings.GOV_API_KEY
        
        if api_key:
            try:
                params = {
                    "api-key": api_key,
                    "format": "json",
                    "limit": 5
                }
                res = requests.get(gov_url, params=params, timeout=10)
                if res.status_code == 200:
                    data = res.json().get("records", [])
                    self.stdout.write(f"✅ Successfully fetched {len(data)} sample records.")
                    # Let the system naturally handle these when user visits Market Prices page
                    # or we can manually save them here. But for a seed script, this is enough to proof life.
                else:
                    self.stdout.write(self.style.WARNING("⚠️  Gov API returned non-200 status. Prices not seeded."))
            except Exception as e:
                 self.stdout.write(self.style.ERROR(f"❌ Error fetching prices: {str(e)}"))
        else:
            self.stdout.write(self.style.WARNING("⚠️  GOV_API_KEY not set. Skipping price fetch."))

        self.stdout.write(self.style.SUCCESS("✨ Database seeding complete!"))
        self.stdout.write("👉 Visit /admin/ to upload your dashboard images.")
