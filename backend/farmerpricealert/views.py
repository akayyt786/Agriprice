from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import authenticate
from datetime import datetime
from django.db import IntegrityError, transaction, models
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import CreateAPIView
from .serializers import RegisterSerializer
from .models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
from .models import (
    SiteContent,
    DashboardImage,
    UserProfile,
    AlertSubscription,
    AlertHistory,
    MarketPrice,
    Crop,
    Market
)
import random
import requests
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from .authenticate import CookieJWTAuthentication

BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
API_KEY = "579b464db66ec23bdd00000162112b7dd11f40117613f282ddc07b6e"

def registration_page(request):
    content = SiteContent.objects.filter(page_name="registration").first()
    return render(request, "registration.html", {"content": content})

def market_prices_page(request):
    return render(request, "marketprices.html")

def dashboard_page(request):
    images = {img.key: img for img in DashboardImage.objects.all()}
    return render(request, "dashboard.html", {"dashboard_images": images})

def login_page(request):
    return render(request, "login.html")


def profile_page(request):
    return render(request, "profile.html")


def logout_user(request):
    request.session.flush()
    return redirect("login_root")


def round_price(value):
    if value is None:
        return None
    return round(float(value) / 100) * 100

def alerts_page(request):
    return render(request, "alertpage.html")



# Get government market prices
@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def gov_market_prices(request):
    crop = request.GET.get("crop", "").strip()
    state = request.GET.get("state", "").strip()
    district = request.GET.get("district", "").strip()
    mandi = request.GET.get("mandi", "").strip()

    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": 1000      # get as much as possible
    }

    # Pass filters directly to the Government API for accurate results
    if state:
        params["filters[state]"] = state.title()
    if district:
        params["filters[district]"] = district.title()
    if crop:
        params["filters[commodity]"] = crop.title()
    if mandi:
        params["filters[market]"] = mandi.title()

    try:
        res = requests.get(BASE_URL, params=params, timeout=10)
        api_failed = (res.status_code != 200)
    except Exception as e:
        print(f"--- ERROR: Gov API Connection Failed: {str(e)}")
        api_failed = True

    if api_failed:
        # FALLBACK: Use local database if Gov API is down
        print("--- WARNING: Gov API down, falling back to local database")
        
        # Build local query based on filters
        local_prices = MarketPrice.objects.select_related("crop", "market").all()
        
        if state:
            local_prices = local_prices.filter(market__state__icontains=state)
        if district:
            local_prices = local_prices.filter(market__district__icontains=district)
        if crop:
            local_prices = local_prices.filter(crop__name__icontains=crop)
        if mandi:
            local_prices = local_prices.filter(market__name__icontains=mandi)
            
        local_prices = local_prices.order_by("-arrival_date")[:1000]
        
        formatted = []
        for p in local_prices:
            formatted.append({
                "date": p.arrival_date.strftime("%d/%m/%Y") if p.arrival_date else "N/A",
                "crop_name": p.crop.name.title(),
                "crop": p.crop.name.title(),
                "mandi_name": p.market.name.title(),
                "commodity": p.crop.name.title(),
                "market": p.market.name.title(),
                "state": p.market.state,
                "district": p.market.district,
                "min_price": str(p.min_price),
                "max_price": str(p.max_price),
                "modal_price": str(p.modal_price),
                "source": "local_cache"
            })
            
        return Response({
            "total": len(formatted),
            "prices": formatted,
            "warning": "External API is currently unavailable. Showing latest cached data."
        })

    data = res.json().get("records", [])

    formatted = []

    def get_field(data_dict, keys):
        for k in keys:
            val = data_dict.get(k)
            if val is not None and val != "":
                return str(val)
        return "N/A"

    for d in data:
        # 1. Robust Local Filtering (Case-Insensitive)
        # We check this FIRST to avoid unnecessary DB work or processing
        curr_state = d.get("state", "").lower()
        curr_dist = d.get("district", "").lower()
        curr_comm = d.get("commodity", "").lower()
        curr_mkt = d.get("market", "").lower()

        if state and state.lower() not in curr_state:
            continue
        if district and district.lower() not in curr_dist:
            continue
        if crop and crop.lower() not in curr_comm:
            continue
        if mandi and mandi.lower() not in curr_mkt:
            continue

        # 2. Database Synchronization
        raw_date = d.get("arrival_date")
        formatted_date = None
        if raw_date:
            try:
                formatted_date = datetime.strptime(raw_date, "%d/%m/%Y").date()
            except:
                formatted_date = None

        if not formatted_date:
            continue
        crop_name_raw = d.get("commodity", "N/A").lower()
        market_name_raw = d.get("market", "N/A").lower()
        crop_obj, _ = Crop.objects.get_or_create(name=crop_name_raw)

        market_obj, created = Market.objects.get_or_create(
            name=market_name_raw,
            defaults={
                "state": d.get("state", "India"),
                "district": d.get("district", market_name_raw)
            }
        )
        
        # 🔥 CRITICAL: Update existing Market if district/state is missing or "N/A"
        dist_raw = d.get("district")
        state_raw = d.get("state")
        
        needs_save = False
        if dist_raw and (not market_obj.district or market_obj.district == "N/A" or market_obj.district == ""):
            market_obj.district = dist_raw
            needs_save = True
        if state_raw and (not market_obj.state or market_obj.state == "N/A" or market_obj.state == ""):
            market_obj.state = state_raw
            needs_save = True
            
        if needs_save:
            market_obj.save()

        price_obj, _ = MarketPrice.objects.get_or_create(
            crop=crop_obj,
            market=market_obj,
            arrival_date=formatted_date,
            defaults={
                "min_price": d.get("min_price"),
                "max_price": d.get("max_price"),
                "modal_price": d.get("modal_price"),
            }
        )

        # Process Alerts
        # Find alerts that match this specific Mandi OR match the District name of this Mandi
        alerts = AlertSubscription.objects.filter(
            models.Q(market=market_obj) | models.Q(market__name__iexact=market_obj.district),
            crop=crop_obj, 
            status="active"
        )
        for alert in alerts:
            message = f"Market Alert: {crop_obj.name.title()} is available in {market_obj.name.title()} mandi at price range {price_obj.min_price}-{price_obj.max_price}."
            process_alert(alert, price_obj, message)

        # 3. Format result for Frontend
        comm = get_field(d, ["commodity", "Commodity"])
        mkt = get_field(d, ["market", "Market"])

        formatted.append({
            "date": d.get("arrival_date", "N/A"),
            "crop_name": comm,
            "crop": comm,
            "mandi_name": mkt,
            "commodity": comm, 
            "market": mkt,
            "state": d.get("state", "N/A"),
            "district": d.get("district", "N/A"),
            "min_price": d.get("min_price", "0"),
            "max_price": d.get("max_price", "0"),
            "modal_price": d.get("modal_price", "0"),
        })

    return Response({
        "total": len(formatted),
        "prices": formatted
    })


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "User registered successfully"},
            status=status.HTTP_201_CREATED
        )



@method_decorator(csrf_exempt, name='dispatch')
class CookieLoginView(APIView):
    def post(self, request):

        # 1. Get username and password from the request
        username = request.data.get("username")
        password = request.data.get("password")

        # 2. Check if the user exists and password is correct
        user = authenticate(username=username, password=password)

        if user is None:
            return JsonResponse({"detail": "Invalid username or password"}, status=401)

        # 3. Create JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # 4. Create a response
        response = JsonResponse({"message": "Login successful"})

        # 5. Save tokens as cookies
        response.set_cookie(
            "access",
            value=str(access),
            httponly=True,   # JavaScript cannot read it
            secure=False,    # change to True when using HTTPS
            samesite="Lax",
            path="/",
        )

        response.set_cookie(
            "refresh",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/",
        )
        return response

@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_past_alerts(request):
    user = request.user

    history = AlertHistory.objects.filter(
        subscription__user=user
    ).order_by("-created_at")

    data = []

    for h in history:
        data.append({
            "crop": h.subscription.crop.name,
            "market": h.subscription.market.name,
            "target_min": str(h.subscription.target_min),
            "target_max": str(h.subscription.target_max),
            "triggered_at": h.created_at.strftime("%Y-%m-%d %H:%M"),
        })

    return Response(data)

@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_alerts(request):
    user = request.user

    # All alerts for user (active + triggered)
    active_alerts = AlertSubscription.objects.filter(
        user=user
    ).order_by("-created_at")

    past_alerts = AlertHistory.objects.filter(
        subscription__user=user
    ).select_related("price", "subscription").order_by("-created_at")

    return Response({
      "active": [
    {
        "id": a.id,
        "crop": a.crop.name,
        "market": a.market.name,
        "target_min": str(a.target_min),
        "target_max": str(a.target_max),
        "status": a.status,
        "created_at": a.created_at.strftime("%Y-%m-%d %H:%M"),
        "current_price": (
            str(
                MarketPrice.objects.filter(
                    models.Q(market=a.market) | models.Q(market__district__iexact=a.market.name),
                    crop=a.crop
                ).order_by("-arrival_date").first().modal_price
            )
            if MarketPrice.objects.filter(
                models.Q(market=a.market) | models.Q(market__district__iexact=a.market.name),
                crop=a.crop
            ).exists()
            else None
        )
    }
    for a in active_alerts
],
        "history": [
            {
                "id": h.id,
                "crop": h.subscription.crop.name,
                "market": h.subscription.market.name,
                "price_reached": str(h.price.modal_price),
                "status": "triggered",
                "date": h.created_at.strftime("%Y-%m-%d %H:%M")
            }
            for h in past_alerts
        ]
    })


def process_alert(alert, price_obj, message):
    user_min = float(alert.target_min)
    user_max = float(alert.target_max)

    prices = [
        round_price(price_obj.min_price),
        round_price(price_obj.modal_price),
        round_price(price_obj.max_price)
    ]

    for p in prices:
        if p is None:
            continue

        if user_min <= p <= user_max:
            alert.status = "triggered"
            alert.save()

            AlertHistory.objects.create(
                subscription=alert,
                price=price_obj,
                message=message
            )

            return True

    return False



@csrf_exempt
@api_view(["POST"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_alert(request):
    user = request.user

    crop_name = request.data.get("crop")
    market_name = request.data.get("market")
    min_price = request.data.get("min_price")
    max_price = request.data.get("max_price")

    if not crop_name or not market_name or not min_price or not max_price:
        return Response({"error": "All fields are required"}, status=400)

    crop_name = crop_name.strip().lower()
    market_name = market_name.strip().lower()

    crop_obj, _ = Crop.objects.get_or_create(name=crop_name)

    # 🔥 MATCH BY DISTRICT FIRST
    market_obj = Market.objects.filter(
        district__icontains=market_name
    ).first()

    if not market_obj:
        market_obj = Market.objects.create(
            name=market_name,
            state="India",
            district=market_name
        )

    alert = AlertSubscription.objects.create(
        user=user,
        crop=crop_obj,
        market=market_obj,
        target_min=min_price,
        target_max=max_price,
    )

    return Response({"message": "Alert created successfully", "id": alert.id})



@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    return Response({
        "full_name": profile.full_name,
        "username": user.username,
        "email": user.email,
        "phone": profile.phone,
        "state": profile.location_state,
        "district": profile.location_district,
        "profile_image": profile.profile_image.url if profile.profile_image else None
    })



@api_view(["POST", "PUT"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
@transaction.atomic
def update_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Handling both form-data (for image) and JSON (for text)
    if request.content_type == 'application/json':
        data = request.data
        profile.full_name = data.get("full_name", profile.full_name)
        profile.phone = data.get("phone", profile.phone)
        profile.location_state = data.get("state", profile.location_state)
        profile.location_district = data.get("district", profile.location_district)
    else:
        profile.full_name = request.POST.get("full_name", profile.full_name)
        profile.phone = request.POST.get("phone", profile.phone)
        profile.location_state = request.POST.get("state", profile.location_state)
        profile.location_district = request.POST.get("district", profile.location_district)
        
        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']

    profile.save()
    return Response({"message": "Profile updated"})



@api_view(["POST"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current = request.data.get("current_password")
    new = request.data.get("new_password")

    if not user.check_password(current):
        return Response({"error": "Wrong current password"}, status=400)

    user.set_password(new)
    user.save()
    return Response({"message": "Password updated"})



@api_view(["POST", "DELETE"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def delete_account(request):
    user = request.user
    user.delete()
    return Response({"message": "Account deleted"})


def logout_user(request):
    response = JsonResponse({"message": "Logged out successfully"})
    response.delete_cookie("access", path="/")
    response.delete_cookie("refresh", path="/")
    return response

