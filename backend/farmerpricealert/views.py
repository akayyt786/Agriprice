from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from django.contrib.auth import logout  
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import jwt
import os
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from datetime import datetime, timedelta
from django.db import IntegrityError, transaction, models
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
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.files.storage import default_storage
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
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from .authenticate import CookieJWTAuthentication

BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
API_KEY = settings.GOV_API_KEY
User = get_user_model()

def reset_password_page(request):
    """Display the reset password form (no auth required)."""
    return render(request, "reset_password.html")

def registration_page(request):
    # If already authenticated, redirect to dashboard
    if _is_authenticated(request):
        return redirect('dashboard')
    content = SiteContent.objects.filter(page_name="registration").first()
    return render(request, "registration.html", {"content": content})

def _is_authenticated(request):
    """Check if user is authenticated via JWT or session."""
    return request.user and request.user.is_authenticated

def _require_login(view_func):
    """Decorator to require authentication for views using JWT cookies."""
    def wrapper(request, *args, **kwargs):
        if not _is_authenticated(request):
            return redirect('login_page')
        return view_func(request, *args, **kwargs)
    return wrapper

@never_cache
@_require_login
def market_prices_page(request):
    return render(request, "marketprices.html")

@never_cache
@_require_login
def dashboard_page(request):
    images = {img.key: img for img in DashboardImage.objects.all()}
    return render(request, "dashboard.html", {"dashboard_images": images})

def login_page(request):
    # If already authenticated, redirect to dashboard
    if _is_authenticated(request):
        return redirect('dashboard')
    return render(request, "login.html")


@never_cache
@_require_login
def profile_page(request):
    return render(request, "profile.html")



def round_price(val):
    """Helper to round price to 2 decimal places safely."""
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return 0.0

@never_cache
@_require_login
def alerts_page(request):
    return render(request, "alertpage.html")


def round_price(value):
    if value is None:
        return None
    return round(float(value) / 100) * 100

@never_cache
@_require_login
def alerts_page(request):
    return render(request, "alertpage.html")

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]       # Allow anyone (even strangers) to access this
    authentication_classes = []

    @transaction.atomic
    def post(self, request):
        print("=" * 50)
        print("REGISTRATION REQUEST RECEIVED")
        print(f"Request data: {request.data}")
        print("=" * 50)
        
        try:
            # Check for duplicate email first
            email = request.data.get('email', '').lower()
            if not email:
                return Response({"error": "Email is required"}, status=400)
                
            if User.objects.filter(email=email).exists():
                return Response(
                    {"error": "A user with this email already exists"}, 
                    status=400
                )
            
            print("Step 1: Validating serializer...")
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            print("Step 1: Serializer valid ✓")
            
            print("Step 2: Saving user...")
            user = serializer.save()
            print(f"Step 2: User created - ID: {user.id}, Username: {user.username}, Email: {user.email}")
            
            print("Step 3: Marking user as inactive...")
            user.is_active = False 
            user.save()
            print("Step 3: User marked inactive ✓")
            
            print("Step 4: Generating JWT token...")
            token = jwt.encode(
                {"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=24)},
                settings.SECRET_KEY,
                algorithm="HS256"
            )
            print(f"Step 4: Token generated ✓")
            
            print("Step 5: Building verification link...")
            site_url = os.getenv('SITE_URL')
            if not site_url:
                print("ERROR: SITE_URL environment variable not set")
                return Response(
                    {"error": "Server configuration error. Please contact support."}, 
                    status=500
                )
            verification_link = f"{site_url}/api/verify-email/{token}/"
            print(f"Step 5: Verification link: {verification_link}")
            
            print("Step 6: Sending email...")
            print(f"From: {settings.DEFAULT_FROM_EMAIL}")
            print(f"To: {user.email}")
            
            try:
                send_mail(
                    subject="Verify your AgriPrice Account",
                    message=f"Hi {user.username},\n\nPlease verify your account by clicking the link below:\n\n{verification_link}\n\nThis link expires in 24 hours.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                print("Step 6: Email sent successfully ✓")
            except Exception as e:
                print(f"Step 6: Email FAILED - {str(e)}")
                
                # FIX: Render blocks outbound SMTP (port 587/465). 
                # Instead of leaving the user locked out (inactive), we auto-activate them.
                user.is_active = True
                user.save()
                
                return Response({
                    "message": "Registration successful! (Email verification skipped due to server restrictions)",
                    "warning": "Email could not be sent. Your account is already active, you can log in immediately.",
                    "user_id": user.id
                }, status=201)
            
            print("SUCCESS: Registration complete!")
            print("=" * 50)
            return Response(
                {"message": "User registered successfully. Please check your email to verify your account.", "token": token},
                status=status.HTTP_201_CREATED
            )
            
        except IntegrityError as e:
            print(f"ERROR: IntegrityError - {str(e)}")
            if 'email' in str(e).lower():
                return Response({"error": "This email is already registered"}, status=400)
            if 'username' in str(e).lower():
                return Response({"error": "This username is already taken"}, status=400)
            return Response({"error": "Registration failed due to duplicate data"}, status=400)
            
        except Exception as e:
            print(f"ERROR: Registration failed - {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            print("=" * 50)
            return Response({"error": "Registration failed. Please try again."}, status=400)


from rest_framework.decorators import api_view, permission_classes, authentication_classes # <--- Import this

@api_view(['GET'])
@permission_classes([])      # No login required
@authentication_classes([])  # <--- ADD THIS: Ignore cookies/auth for this view
def verify_email(request, token):
    try:
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user = User.objects.get(id=payload['user_id'])
        
        if user.is_active:
            return redirect('/login/?verified=already')
            
        user.is_active = True
        user.save()
        
        return redirect('/login/?verified=true')
        
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Activation link expired'}, status=400)
    except jwt.DecodeError:
        return JsonResponse({'error': 'Invalid token'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@never_cache
@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def list_markets(request):
    markets = Market.objects.all().order_by("name")

    return Response([
        {
            "id": str(m.id),  # Return as string to preserve precision for large CockroachDB IDs
            "name": m.name.title(),
            "district": m.district,
            "state": m.state
        }
        for m in markets
    ])

@method_decorator(csrf_exempt, name='dispatch')
class CookieLoginView(APIView):
    # 1. ALLOW ANONYMOUS ACCESS (Critical Fix)
    permission_classes = [AllowAny]
    authentication_classes = [] 

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return JsonResponse({"detail": "Username and password are required"}, status=400)

        # 2. CHECK FOR INACTIVE USERS (Critical Fix)
        User = get_user_model()
        user_obj = User.objects.filter(username=username).first()

        if user_obj is not None:
            # If user exists, check password manually
            if user_obj.check_password(password):
                # If password is correct but account is inactive
                if not user_obj.is_active:
                    return JsonResponse(
                        {"detail": "Account is inactive. Please check your email to verify."}, 
                        status=401
                    )
            else:
                 # User exists but password is wrong
                 return JsonResponse({"detail": "Invalid username or password"}, status=401)
        
        # 3. STANDARD AUTHENTICATION
        # (If we get here, the user is either active or doesn't exist)
        user = authenticate(username=username, password=password)

        if user is None:
            return JsonResponse({"detail": "Invalid username or password"}, status=401)

        # 4. GENERATE TOKENS
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # 5. SET COOKIES
        response = JsonResponse({"message": "Login successful"})
        is_secure = not settings.DEBUG  # True in production (HTTPS)
        
        response.set_cookie(
            "access",
            value=str(access),
            httponly=True,
            secure=is_secure,
            samesite="Lax",
            path="/"
        )

        response.set_cookie(
            "refresh",
            value=str(refresh),
            httponly=True,
            secure=is_secure,
            samesite="Lax",
            path="/"
        )
        
        return response

def _sync_all_mandi_prices():
    """
    Fetch ALL mandi prices for today from Gov API and save to local database.
    Uses curl subprocess because Python requests times out on some networks.
    Also cleans up data older than 7 days.
    """
    import subprocess, json as json_mod
    
    today = datetime.now().date()
    limit = 500  # Fetch in large chunks to minimize API calls
    offset = 0
    total_saved = 0

    print(f"--- SYNC START: Fetching all records for {today}")

    while True:
        url = f"{BASE_URL}?api-key={API_KEY}&format=json&limit={limit}&offset={offset}"
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "120", url],
                capture_output=True, text=True, timeout=130
            )
            
            if result.returncode != 0:
                print(f"--- SYNC ERROR: curl failed with code {result.returncode}")
                break
            
            data_json = json_mod.loads(result.stdout)
            records = data_json.get("records", [])
            total_available = data_json.get("total", 0)

            if not records:
                break

            for d in records:
                raw_date = d.get("arrival_date")
                try:
                    formatted_date = datetime.strptime(raw_date, "%d/%m/%Y").date() if raw_date else None
                except:
                    continue

                if not formatted_date:
                    continue

                # Resolve Crop & Market
                crop_name = d.get("commodity", "N/A").lower()
                market_name = d.get("market", "N/A").lower()
                
                crop_obj, _ = Crop.objects.get_or_create(name=crop_name)
                market_obj, _ = Market.objects.get_or_create(
                    name=market_name,
                    defaults={
                        "state": d.get("state", "India"),
                        "district": d.get("district", market_name)
                    }
                )
                
                # Update state/district if they were missing
                updated = False
                if d.get("state") and (not market_obj.state or market_obj.state == "India"):
                    market_obj.state = d.get("state")
                    updated = True
                if d.get("district") and (not market_obj.district or market_obj.district == market_name):
                    market_obj.district = d.get("district")
                    updated = True
                if updated:
                    market_obj.save()

                # Save Price
                _, created = MarketPrice.objects.get_or_create(
                    crop=crop_obj,
                    market=market_obj,
                    arrival_date=formatted_date,
                    defaults={
                        "min_price": d.get("min_price"),
                        "max_price": d.get("max_price"),
                        "modal_price": d.get("modal_price")
                    }
                )
                if created:
                    total_saved += 1

            print(f"--- SYNC PROGRESS: Processed {offset + len(records)} / {total_available}")
            
            if (offset + len(records)) >= total_available:
                break
            
            offset += limit
        except Exception as e:
            print(f"--- SYNC EXCEPTION at offset {offset}: {str(e)}")
            break

    # CLEANUP: Remove data older than 7 days
    seven_days_ago = today - timedelta(days=7)
    deleted_count, _ = MarketPrice.objects.filter(arrival_date__lt=seven_days_ago).delete()
    print(f"--- SYNC COMPLETE: Saved {total_saved} new records. Deleted {deleted_count} old records.")
    
    return total_saved


@api_view(["GET"])
@permission_classes([AllowAny]) # Allow your external Cron/Pinger to hit this
@authentication_classes([])
def sync_daily_data(request):
    """
    Dedicated endpoint for your external cron-job to trigger a full sync.
    """
    # Security: You can add a secret key check here if you want
    # if request.GET.get('key') != 'your_secret_key': return Response(status=403)
    
    saved_count = _sync_all_mandi_prices()
    return Response({
        "status": "success",
        "message": f"Synchronized {saved_count} new records for today.",
        "date": datetime.now().date()
    })


# Get government market prices
@never_cache
@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def gov_market_prices(request):
    crop = request.GET.get("crop", "").strip()
    state = request.GET.get("state", "").strip()
    district = request.GET.get("district", "").strip()
    mandi = request.GET.get("mandi", "").strip()
    
    # Pagination Parameters
    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1
    
    limit = 10
    offset = (page - 1) * limit

    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": limit,
        "offset": offset
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

    # 1. LOCAL-FIRST: Check if we have data in local DB matching the filters
    today = datetime.now().date()
    
    # Build local query based on filters
    local_query = MarketPrice.objects.select_related("crop", "market").all()
    if state:
        local_query = local_query.filter(market__state__icontains=state)
    if district:
        local_query = local_query.filter(market__district__icontains=district)
    if crop:
        local_query = local_query.filter(crop__name__icontains=crop)
    if mandi:
        local_query = local_query.filter(market__name__icontains=mandi)

    # Check if we have TODAY's data for this specific query locally
    has_today_data = local_query.filter(arrival_date=today).exists()

    if has_today_data:
        # Today's data found locally — return it instantly (fastest path)
        total_count = local_query.count()
        local_prices = local_query.order_by("-arrival_date")[offset:offset+limit]
        
        formatted = []
        for p in local_prices:
            formatted.append({
                "date": p.arrival_date.strftime("%d/%m/%Y"),
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
            "total": total_count,
            "page": page,
            "prices": formatted,
            "cached": True
        })

    # 2. BROAD FALLBACK: If specific filters found nothing for today, try just state-level
    if state:
        broad_query = MarketPrice.objects.select_related("crop", "market").filter(
            market__state__icontains=state,
            arrival_date=today
        )
        # Also filter by crop if provided
        if crop:
            broad_query = broad_query.filter(crop__name__icontains=crop)
        
        if broad_query.exists():
            total_count = broad_query.count()
            local_prices = broad_query.order_by("-arrival_date")[offset:offset+limit]
            
            formatted = []
            for p in local_prices:
                formatted.append({
                    "date": p.arrival_date.strftime("%d/%m/%Y"),
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
                    "source": "state_fallback"
                })
            
            info_msg = f"No exact results for"
            if district:
                info_msg += f" district '{district}'"
            if mandi:
                info_msg += f" mandi '{mandi}'"
            info_msg += f". Showing all available prices in {state.title()}."
            
            return Response({
                "total": total_count,
                "page": page,
                "prices": formatted,
                "cached": True,
                "info": info_msg
            })

    # 3. GENERAL FALLBACK: Show any available data sorted by newest
    any_today = MarketPrice.objects.filter(arrival_date=today).exists()
    if any_today:
        all_today = MarketPrice.objects.select_related("crop", "market").filter(
            arrival_date=today
        )
        if crop:
            all_today = all_today.filter(crop__name__icontains=crop)
        
        total_count = all_today.count()
        local_prices = all_today.order_by("-arrival_date")[offset:offset+limit]
        
        formatted = []
        for p in local_prices:
            formatted.append({
                "date": p.arrival_date.strftime("%d/%m/%Y"),
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
                "source": "general_fallback"
            })
        
        return Response({
            "total": total_count,
            "page": page,
            "prices": formatted,
            "cached": True,
            "info": f"No exact match found. Showing available prices for today."
        })

    # 4. NO LOCAL DATA AT ALL: Try Gov API (last resort) using curl
    import subprocess, json as json_mod, urllib.parse
    api_failed = False
    try:
        # Build URL with params for curl
        query_string = urllib.parse.urlencode(params)
        full_url = f"{BASE_URL}?{query_string}"
        result = subprocess.run(
            ["curl", "-s", "--max-time", "60", full_url],
            capture_output=True, text=True, timeout=65
        )
        if result.returncode != 0 or not result.stdout.strip():
            api_failed = True
        else:
            res_json = json_mod.loads(result.stdout)
    except Exception as e:
        print(f"--- ERROR: Gov API Connection Failed: {str(e)}")
        api_failed = True

    if api_failed:
        # Ultimate fallback: Return whatever we have in the local DB (any date)
        all_local = MarketPrice.objects.select_related("crop", "market").all()
        total_count = all_local.count()
        local_prices = all_local.order_by("-arrival_date")[offset:offset+limit]
        
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
                "source": "local_cache_fallback"
            })
            
        return Response({
            "total": total_count,
            "page": page,
            "prices": formatted,
            "warning": "External API currently unavailable. Showing latest cached data."
        })

    data = res_json.get("records", [])
    total_records = res_json.get("total", 0)

    
    formatted = []

    def get_field(data_dict, keys):
        for k in keys:
            val = data_dict.get(k)
            if val is not None and val != "":
                return str(val)
        return "N/A"

    for d in data:
        # 1. Filtering (Redundant if API handled it, but good for safety if API ignores cache mismatch)
        curr_state = d.get("state", "").lower()
        curr_dist = d.get("district", "").lower()
        curr_comm = d.get("commodity", "").lower()
        curr_mkt = d.get("market", "").lower()

        if state and state.lower() not in curr_state: continue
        if district and district.lower() not in curr_dist: continue
        if crop and crop.lower() not in curr_comm: continue
        if mandi and mandi.lower() not in curr_mkt: continue

        # 2. Date Parsing
        raw_date = d.get("arrival_date")
        try:
            formatted_date = datetime.strptime(raw_date, "%d/%m/%Y").date() if raw_date else None
        except:
            formatted_date = None
        
        if not formatted_date: continue
            
        # 3. Resolve Crop/Market & Save
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
        
        # Update details if missing
        if d.get("district") and (not market_obj.district or market_obj.district == "N/A"):
             market_obj.district = d.get("district")
             market_obj.save()
        if d.get("state") and (not market_obj.state or market_obj.state == "N/A"):
             market_obj.state = d.get("state")
             market_obj.save()

        # Save Price
        price_obj, created_price = MarketPrice.objects.get_or_create(
            crop=crop_obj,
            market=market_obj,
            arrival_date=formatted_date,
            defaults={
                "min_price": d.get("min_price"),
                "max_price": d.get("max_price"),
                "modal_price": d.get("modal_price")
            }
        )

        # Process Alerts (Only for newly created prices)
        if created_price:
            # Find alerts matching this crop (case-insensitive) and market
            alerts = AlertSubscription.objects.filter(
                models.Q(market=market_obj) | models.Q(market__name__iexact=market_obj.name),
                crop__name__iexact=crop_obj.name, 
                status="active"
            )
            for alert in alerts:
                message = f"Market Alert: {crop_obj.name.title()} is available in {market_obj.name.title()} mandi at price range {price_obj.min_price}-{price_obj.max_price}."
                process_alert(alert, price_obj, message)

        # Frontend format
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
        "total": total_records, # May be None/0 if API doesn't send it, frontend should handle
        "page": page,
        "prices": formatted
    })





@never_cache
@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_past_alerts(request):
    user = request.user

    history = AlertHistory.objects.filter(
        subscription__user=user
    ).select_related("subscription", "subscription__crop", "subscription__market").order_by("-created_at")

    data = []

    for h in history:
        data.append({
            "crop": h.subscription.crop.name.title(),
            "market": h.subscription.market.name.title(),
            "target_min": str(h.subscription.target_min),
            "target_max": str(h.subscription.target_max),
            "triggered_at": h.created_at.strftime("%Y-%m-%d %H:%M"),
        })

    return Response(data)

@never_cache
@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_alerts(request):
    user = request.user

    # 1. Fetch all subscriptions for this user (including triggered ones for reprocessing)
    all_alerts = AlertSubscription.objects.filter(
        user=user
    ).select_related('crop', 'market').order_by("-created_at")

    active_data = []

    # 2. Process ALL alerts to see if any need triggering NOW
    for a in all_alerts:
        if a.status != 'active':
            continue

        current_price_val = None
        try:
            # Try to find the latest price for this specific market and crop
            # Use case-insensitive matching for crop name and check both market ID and name
            latest_price_obj = MarketPrice.objects.filter(
                crop__name__iexact=a.crop.name,
                market=a.market
            ).order_by("-arrival_date").first()
            
            # If no exact market match, try by market name (case-insensitive)
            if not latest_price_obj:
                latest_price_obj = MarketPrice.objects.filter(
                    crop__name__iexact=a.crop.name,
                    market__name__iexact=a.market.name
                ).order_by("-arrival_date").first()
            
            if latest_price_obj:
                p_min = round_price(latest_price_obj.min_price)
                p_max = round_price(latest_price_obj.max_price)
                current_price_val = f"{p_min} - {p_max}"

                # CHECK TRIGGER CONDITION
                message = f"Market Alert: {a.crop.name.title()} is available in {a.market.name.title()} mandi at price range {p_min}-{p_max}."
                is_triggered = process_alert(a, latest_price_obj, message)
                
                if is_triggered:
                    # If triggered, it's no longer active, so don't add to active_data
                    continue
            else:
                current_price_val = "No data yet"
        except Exception as e:
            print(f"Error processing alert {a.id}: {e}")
            # Ensure it's still added to active/list so user can see it even if check failed
            current_price_val = "Error checking"

        active_data.append({
            "id": str(a.id),  # Store as string for API consistency
            "crop": a.crop.name.title(),
            "market": a.market.name.title(),
            "target_min": str(a.target_min),
            "target_max": str(a.target_max),
            "status": a.status,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M"),
            "current_price": current_price_val
        })

    # 3. Fetch history of triggered alerts (now including the ones we just triggered)
    past_alerts = AlertHistory.objects.filter(
        subscription__user=user
    ).select_related("price", "subscription", "subscription__crop", "subscription__market").order_by("-created_at")

    # 4. Return the response
    return Response({
        "active": active_data,
        "history": [
            {
                "id": str(h.id),  # Store as string for API consistency
                "crop": h.subscription.crop.name.title(),
                "market": h.subscription.market.name.title(),
                "price_reached": str(h.price.modal_price if h.price else "N/A"),
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

            # Send notification email using user.email
            user_email = alert.user.email  # comes from the User model
            if user_email:
                try:
                    send_mail(
                        subject="Market Alert Triggered",
                        message=(
                            f"Hello {alert.user.username},\n\n"
                            f"Your alert for {alert.crop.name.title()} at {alert.market.name.title()} "
                            f"has been triggered.\n\n"
                            f"Price range hit: {p}\n"
                            f"Min: {round_price(price_obj.min_price)}\n"
                            f"Modal: {round_price(price_obj.modal_price)}\n"
                            f"Max: {round_price(price_obj.max_price)}\n"
                            f"Date: {price_obj.arrival_date}\n\n"
                            "Thank you."
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user_email],
                        fail_silently=True,  # set to False if you want to surface errors
                    )
                except Exception:
                    # optionally log the failure
                    pass

            return True

    return False


@never_cache
@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """Return recent alert notifications and unseen count for the current user."""
    user = request.user

    unseen_count = AlertHistory.objects.filter(
        subscription__user=user,
        is_seen=False
    ).count()

    recent_alerts = (
        AlertHistory.objects
        .filter(subscription__user=user)
        .select_related("subscription", "price")
        .order_by("-created_at")[:20]
    )

    items = []
    for alert in recent_alerts:
        sub = alert.subscription
        price = alert.price
        items.append({
            "id": alert.id,
            "message": alert.message,
            "crop": sub.crop.name,
            "market": sub.market.name,
            "price": str(price.modal_price) if price else None,
            "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M"),
            "is_seen": alert.is_seen,
        })

    return Response({
        "unseen_count": unseen_count,
        "items": items
    })


@never_cache
@csrf_exempt
@api_view(["POST"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def mark_notifications_seen(request):
    """Mark all notifications as seen for the current user."""
    user = request.user

    updated = AlertHistory.objects.filter(
        subscription__user=user,
        is_seen=False
    ).update(is_seen=True)

    return Response({
        "updated": updated,
        "unseen_count": 0
    })

#for deleting alert
@never_cache
@api_view(["DELETE"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def delete_alert(request, alert_id):
    user = request.user

    alert = AlertSubscription.objects.filter(id=alert_id, user=user).first()

    if not alert:
        return Response({"error": "Alert not found"}, status=404)

    alert.delete()

    return Response({"message": "Alert deleted"})


#for updating alert
@never_cache
@api_view(["PUT"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def update_alert(request, alert_id):
    user = request.user

    # Convert alert_id to integer for database lookup
    try:
        alert_id = int(alert_id)
    except (ValueError, TypeError):
        return Response({"error": f"Invalid alert ID format: {alert_id}"}, status=400)

    alert = AlertSubscription.objects.filter(id=alert_id, user=user).first()

    if not alert:
        return Response({"error": f"Alert not found (ID: {alert_id})"}, status=404)

    min_price = request.data.get("min_price")
    max_price = request.data.get("max_price")

    if not min_price or not max_price:
        return Response({"error": "Prices are required"}, status=400)

    alert.target_min = min_price
    alert.target_max = max_price
    alert.save()

    return Response({"message": "Alert updated"})



@never_cache
@csrf_exempt
@api_view(["POST"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_alert(request):
    user = request.user

    crop_name = request.data.get("crop")
    market_id = request.data.get("market_id")
    min_price = request.data.get("min_price")
    max_price = request.data.get("max_price")

    if not crop_name or not market_id or not min_price or not max_price:
        return Response({"error": "All fields are required"}, status=400)

    # Normalize crop name to lowercase to match how gov API stores crops
    crop_name_normalized = crop_name.strip().lower()
    crop_obj, _ = Crop.objects.get_or_create(name=crop_name_normalized)

    # Convert market_id to integer if it's a string
    try:
        market_id = int(market_id)
    except (ValueError, TypeError):
        return Response({"error": f"Invalid market ID format: {market_id}"}, status=400)

    market_obj = Market.objects.filter(id=market_id).first()

    if not market_obj:
        # Debug: Return available market count
        market_count = Market.objects.count()
        return Response({"error": f"Invalid market selected (ID: {market_id}). Total markets in DB: {market_count}"}, status=400)

    alert = AlertSubscription.objects.create(
        user=user,
        crop=crop_obj,
        market=market_obj,
        target_min=min_price,
        target_max=max_price,
    )

    return Response({"message": "Alert created successfully", "id": alert.id})


@never_cache
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



@never_cache
@api_view(["POST", "PUT"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
@transaction.atomic
def update_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    old_image_path = profile.profile_image.name if profile.profile_image else None

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

    # Remove previously stored image after successful save (if a new one was uploaded)
    if 'profile_image' in request.FILES and old_image_path and old_image_path != profile.profile_image.name:
        default_storage.delete(old_image_path)

    return Response({"message": "Profile updated"})



@never_cache
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



@never_cache
@api_view(["POST", "DELETE"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def delete_account(request):
    user = request.user
    user.delete()
    return Response({"message": "Account deleted"})

def logout_user(request):
    """
    Logout procedure that handles BOTH:
    1. JWT Cookies (Custom Auth)
    2. Django Session (Google Auth)
    """
    
    # 1. Kill the Django Session (Logs out Google Users)
    if request.user.is_authenticated:
        logout(request)

    # 2. Prepare response to clear JWT cookies
    response = JsonResponse({
        "message": "Logged out successfully",
        "redirect": "/login/"
    })
    
    # 3. Kill the JWT Cookies (Logs out Password Users)
    # We set these to expire immediately
    response.set_cookie("access", "", max_age=0, expires="Thu, 01 Jan 1970 00:00:00 GMT", path="/", samesite="Lax", httponly=True, secure=False)
    response.set_cookie("refresh", "", max_age=0, expires="Thu, 01 Jan 1970 00:00:00 GMT", path="/", samesite="Lax", httponly=True, secure=False)
    
    return response


@never_cache
@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_dashboard_prices(request):
    """
    Fetches:
    1. Table Data: The 5 most recent price updates from the DB.
    2. Card Data: The latest price for specific crops (Wheat, Rice, etc.) from the DB.
    """
    user = request.user
    profile = UserProfile.objects.filter(user=user).first()
    
    # Base query filtered by user's location (optional but recommended)
    base_query = MarketPrice.objects.select_related("crop", "market")
    
    if profile:
        if profile.location_state:
            base_query = base_query.filter(market__state__icontains=profile.location_state)
        if profile.location_district:
            base_query = base_query.filter(market__district__icontains=profile.location_district)
        
    # --- PART 1: Table Data (Strictly latest 5 records) ---
    latest_prices = base_query.order_by("-arrival_date")[:5]
    table_data = []
    for p in latest_prices:
        table_data.append({
            "crop_name": p.crop.name.title(),
            "state": p.market.state,
            "district": p.market.district,
            "min_price": str(p.min_price),
            "max_price": str(p.max_price),
            "date": p.arrival_date.strftime("%d/%m/%Y") if p.arrival_date else "N/A"
        })

    # --- PART 2: Card Data (Specific Crops) ---
    card_targets = ["wheat", "rice", "cotton", "soybean", "sugarcane"]
    card_data = {}

    for target in card_targets:
        # custom logic to handle variations like Rice/Paddy or Soybean/Soyabean
        query_filter = models.Q(crop__name__icontains=target)
        if target == "rice":
            query_filter |= models.Q(crop__name__icontains="paddy")
        elif target == "soybean":
            query_filter |= models.Q(crop__name__icontains="soyabean")

        # Get the single latest price for this crop
        price = base_query.filter(query_filter).order_by("-arrival_date").first()
        
        if price:
            card_data[target] = {
                "name": price.crop.name.title(),
                "price": f"₹{price.modal_price}/quintal"
            }
        else:
            card_data[target] = None

    return Response({
        "table_data": table_data,
        "card_data": card_data
    })


# ==========================
#  PASSWORD RESET ENDPOINTS
# ==========================
class PasswordResetRequestView(APIView):
    """
    POST: User submits email to request password reset link.
    Returns generic success message regardless of user existence (avoid email enumeration).
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        
        if not email:
            return Response(
                {"detail": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.filter(email__iexact=email).first()
        
        if user:
            # Generate token and uid
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_RESET_URL}?uid={uid}&token={token}"
            
            # Send email
            try:
                send_mail(
                    subject="Reset your password",
                    message=(
                        f"Hi {user.username},\n\n"
                        f"Click the link below to reset your password:\n"
                        f"{reset_url}\n\n"
                        f"This link expires in 1 hour.\n\n"
                        f"If you didn't request this, ignore this email."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email send failed: {str(e)}")
                # Don't reveal the error to avoid email enumeration
        
        # Generic response regardless of user existence
        return Response({
            "detail": "If that account exists, we've sent password reset instructions to your email."
        })


class PasswordResetConfirmView(APIView):
    """
    POST: User submits uid, token, and new_password to reset their password.
    Validates token and sets new password.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        
        if not (uidb64 and token and new_password):
            return Response(
                {"detail": "uid, token, and new_password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password strength (Django's validators will be applied via set_password)
        if len(new_password) < 8:
            return Response(
                {"detail": "Password must be at least 8 characters long"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Decode uid
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid reset link"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check token validity
        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response(
                {"detail": "Invalid or expired reset link"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({
            "detail": "Your password has been successfully reset. You can now log in with your new password."
        })


