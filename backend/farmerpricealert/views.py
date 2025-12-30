from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import CreateAPIView
from .serializers import RegisterSerializer
from .models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
from .models import SiteContent
from .models import DashboardImage
import random
import requests

from rest_framework.decorators import api_view
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

# Get government market prices
@api_view(["GET"])
def gov_market_prices(request):
    crop = request.GET.get("crop")
    state = request.GET.get("state")
    district = request.GET.get("district")

    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": 1000      # get as much as possible
    }

    res = requests.get(BASE_URL, params=params)

    if res.status_code != 200:
        return Response({"error": "Gov API not responding"}, status=500)

    data = res.json().get("records", [])

    # FILTERS
    if crop:
        data = [d for d in data if crop.lower() in d.get("commodity", "").lower()]

    if state:
        data = [d for d in data if state.lower() in d.get("state", "").lower()]

    if district:
        data = [d for d in data if district.lower() in d.get("district", "").lower()]

    formatted = []

    for d in data:
        formatted.append({
            "crop": d.get("commodity"),
            "market": d.get("market"),
            "state": d.get("state"),
            "district": d.get("district"),
            "min_price": d.get("min_price"),
            "max_price": d.get("max_price"),
            "modal_price": d.get("modal_price"),
            "date": d.get("arrival_date"),
        })

    return Response({"prices": formatted})


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
        )

        response.set_cookie(
            "refresh",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax",
        )

        return response

