from django.urls import path
from .views import (
    registration_page,
    dashboard_page,
    login_page,
    RegisterView,
    CookieLoginView,
    logout_user,
    gov_market_prices,
    market_prices_page,
    profile_page,
    alerts_page,get_profile,get_alerts,create_alert,get_past_alerts,list_markets,delete_alert,update_alert,get_dashboard_prices
)
from django.views.decorators.csrf import csrf_exempt
from .views import update_profile, change_password, delete_account
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from .authenticate import CookieJWTAuthentication

urlpatterns = [
    path("", login_page, name="login_root"),
    path("register/", registration_page, name="register_page"),
    path("login/", login_page, name="login_page"),
    path("profile/", profile_page, name="profile_page"),
    path("alerts/", alerts_page, name="alerts_page"),
   




   
    # APIs  ❗ JSON ENDPOINT
    
    path("api/register/", csrf_exempt(RegisterView.as_view()), name="register_api"),
    path("api/login-cookie/", CookieLoginView.as_view(), name="cookie_login"),
    path("api/logout/", logout_user, name="logout_api"),
    path("api/profile/me/", get_profile, name="get_profile"),
    path("api/profile/update/", update_profile, name="update_profile"),
    path("api/profile/change-password/", change_password, name="change_password"),
    path("api/profile/delete/", delete_account, name="delete_account"),
    path("api/alerts/", get_alerts, name="get_alerts"),
    path("api/alerts/create/", create_alert, name="create_alert"),
    path("api/markets/", list_markets, name="list_markets"),
    path("api/alerts/past/", get_past_alerts, name="past-alerts"),
    path("api/alerts/<int:alert_id>/delete/", delete_alert, name="delete_alert"),
    path("api/alerts/<int:alert_id>/update/", update_alert, name="update_alert"),

    # ⭐ THIS ONE RETURNS JSON (DATA)
    path("api/market-prices/recent/", get_dashboard_prices, name="get_dashboard_prices"),
    path("api/gov/market-prices/", gov_market_prices, name="gov_market_prices"),

    path("dashboard/", dashboard_page, name="dashboard"),

    # ⭐ THIS ONE RETURNS HTML PAGE (YOUR UI)
    path("market-prices/", market_prices_page, name="market_prices_page"),
]

