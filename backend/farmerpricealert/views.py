from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import authenticate
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
from .models import SiteContent
from .models import DashboardImage,UserProfile
import random
import requests
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from .authenticate import CookieJWTAuthentication
from .models import AlertSubscription, AlertHistory, MarketPrice
from .models import Crop, Market

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

    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": 1000      # get as much as possible
    }

    # Pass filters directly to the Government API for accurate results
    # Convert to title case since Gov API is case-sensitive
    if state:
        params["filters[state]"] = state.title()
    if district:
        params["filters[district]"] = district.title()
    if crop:
        params["filters[commodity]"] = crop.title()

    res = requests.get(BASE_URL, params=params)

    if res.status_code != 200:
        return Response({"error": "Gov API not responding"}, status=500)

    data = res.json().get("records", [])

    formatted = []

    for d in data:
        formatted.append({
            "crop": d.get("commodity"),
            "variety": d.get("variety"),
            "grade": d.get("grade"),
            "market": d.get("market"),
            "state": d.get("state"),
            "district": d.get("district"),
            "min_price": d.get("min_price"),
            "max_price": d.get("max_price"),
            "modal_price": d.get("modal_price"),
            "date": d.get("arrival_date"),
        })

    return Response({
        "total": len(formatted),
        "prices": formatted
    })


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer

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
def get_alerts(request):
    user = request.user

    active_alerts = AlertSubscription.objects.filter(user=user)

    past_alerts = AlertHistory.objects.filter(
        subscription__user=user
    ).select_related("price", "subscription")

    return Response({
        "active": [
            {
                "id": a.id,
                "crop": a.crop.name,
                "market": a.market.name,
                "target_min": str(a.target_min),
                "target_max": str(a.target_max),
                "status": a.status,
                "created_at": a.created_at
            }
            for a in active_alerts
        ],
        "history": [
            {
                "id": h.id,
                "crop": h.subscription.crop.name,
                "market": h.subscription.market.name,
                "price_reached": str(h.price.modal_price),
                "status": h.subscription.status,
                "date": h.created_at
            }
            for h in past_alerts
        ]
    })
@csrf_exempt
@api_view(["POST"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def create_alert(request):
    user = request.user

    # Get the names typed by the user
    crop_name = request.data.get("crop")
    market_name = request.data.get("market")
    min_price = request.data.get("min_price")
    max_price = request.data.get("max_price")

    if not crop_name or not market_name or not min_price or not max_price:
        return Response({"error": "All fields are required"}, status=400)

    # 1. Find the Crop (or create it if it doesn't exist)
    crop_obj, _ = Crop.objects.get_or_create(name__iexact=crop_name, defaults={'name': crop_name})
    
    # 2. Find the Market (or create it if it doesn't exist)
    market_obj, _ = Market.objects.get_or_create(
        name__iexact=market_name, 
        defaults={'name': market_name, 'state': 'India', 'district': market_name}
    )

    # 3. Create the Alert using the OBJECTS we found above
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

