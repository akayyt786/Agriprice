
import os
import django
import sys

# Setup Django standalone
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from farmerpricealert.models import AlertSubscription, MarketPrice, Market, Crop
from django.db.models import Q

def check():
    print("--- Checking Active Alerts ---")
    alerts = AlertSubscription.objects.filter(status='active')
    
    if not alerts.exists():
        print("No active alerts found.")
        return

    for a in alerts:
        print(f"\nAlert ID: {a.id}")
        print(f"  User: {a.user.username}")
        print(f"  Crop: '{a.crop.name}' (ID: {a.crop.id})")
        print(f"  Market: '{a.market.name}' (ID: {a.market.id})")
        
        # 1. Direct Logic Check
        match = MarketPrice.objects.filter(
            Q(market=a.market) | Q(market__name__iexact=a.market.name),
            crop__name__iexact=a.crop.name
        ).order_by("-arrival_date").first()
        
        if match:
            print(f"  [SUCCESS] Match found: {match.min_price}-{match.max_price} on {match.arrival_date}")
        else:
            print("  [FAILURE] No match found with current logic.")
            
            # Debugging why
            # Check if ANY price exists for this crop
            any_crop_prices = MarketPrice.objects.filter(crop=a.crop).count()
            print(f"  Debug: Total prices for crop '{a.crop.name}': {any_crop_prices}")
            
            if any_crop_prices > 0:
                # Check what markets have prices for this crop
                price_markets = MarketPrice.objects.filter(crop=a.crop).values_list('market__name', flat=True).distinct()
                print(f"  Debug: Markets having '{a.crop.name}' prices: {list(price_markets)}")
                
                # Check casing issues
                for exist_mk in price_markets:
                    if exist_mk.lower() == a.market.name.lower():
                        print(f"  !!! POTENTIAL MATCH FOUND: '{exist_mk}' (Case mismatch?)")
                        
            # Check if ANY price exists for this market (regardless of crop)
            any_mkt_prices = MarketPrice.objects.filter(market=a.market).count()
            print(f"  Debug: Total prices for market '{a.market.name}' (exact ID): {any_mkt_prices}")
            
            name_matches = MarketPrice.objects.filter(market__name__iexact=a.market.name).count()
            print(f"  Debug: Total prices for market '{a.market.name}' (name match): {name_matches}")

            # Check Crop Casing confusion
            # Is there another crop with same name but different case?
            similar_crops = Crop.objects.filter(name__iexact=a.crop.name).exclude(id=a.crop.id)
            for sc in similar_crops:
                print(f"  !!! Found similar crop: '{sc.name}' (ID: {sc.id})")
                sc_prices = MarketPrice.objects.filter(crop=sc, market__name__iexact=a.market.name).count()
                print(f"      Prices for '{sc.name}' in this market: {sc_prices}")

if __name__ == "__main__":
    check()
