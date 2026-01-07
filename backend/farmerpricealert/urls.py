from django.urls import path
from .views import (
    registration_page,
    dashboard_page,
    login_page,
    reset_password_page,
    RegisterView,
    CookieLoginView,
    logout_user,
    gov_market_prices,
    market_prices_page,
    profile_page,
    alerts_page,get_profile,get_alerts,create_alert,get_past_alerts,list_markets,delete_alert,update_alert,get_dashboard_prices,get_notifications,mark_notifications_seen,
    PasswordResetRequestView,
    PasswordResetConfirmView
)
from django.views.decorators.csrf import csrf_exempt
from .views import update_profile, change_password, delete_account
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from .authenticate import CookieJWTAuthentication
from .views import verify_email
from django.contrib.auth import views as auth_views
urlpatterns = [
    path("", login_page, name="login_root"),
    path("register/", registration_page, name="register_page"),
    path("login/", login_page, name="login_page"),
    path("reset-password/", reset_password_page, name="reset_password_page"),
    path("profile/", profile_page, name="profile_page"),
    path("alerts/", alerts_page, name="alerts_page"),
    path("dashboard/", dashboard_page, name="dashboard"),
    path("market-prices/", market_prices_page, name="market_prices_page"),
    # Password Reset URLs
    path("password-reset/",
         auth_views.PasswordResetView.as_view(
             template_name="password_reset_form.html"
         ),
         name="password_reset"),
    path("password-reset/done/",
         auth_views.PasswordResetDoneView.as_view(
             template_name="password_reset_done.html"
         ),
         name="password_reset_done"),
    path("reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(
             template_name="password_reset_confirm.html"
         ),
         name="password_reset_confirm"),
    path("reset/done/",
         auth_views.PasswordResetCompleteView.as_view(
             template_name="password_reset_complete.html"
         ),
         name="password_reset_complete"),




   
    # APIs  ❗ JSON ENDPOINT
    
    path("api/register/", csrf_exempt(RegisterView.as_view()), name="register_api"),
    path("api/login-cookie/", CookieLoginView.as_view(), name="cookie_login"),
    path("api/logout/", logout_user, name="logout_api"),
    path("api/password-reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("api/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("api/profile/me/", get_profile, name="get_profile"),
    path("api/profile/update/", update_profile, name="update_profile"),
    path("api/profile/change-password/", change_password, name="change_password"),
    path("api/profile/delete/", delete_account, name="delete_account"),
    path("api/notifications/", get_notifications, name="get_notifications"),
    path("api/notifications/mark-seen/", mark_notifications_seen, name="mark_notifications_seen"),
    path("api/alerts/", get_alerts, name="get_alerts"),
    path("api/alerts/create/", create_alert, name="create_alert"),
    path("api/markets/", list_markets, name="list_markets"),
    path("api/alerts/past/", get_past_alerts, name="past-alerts"),
    path("api/alerts/<int:alert_id>/delete/", delete_alert, name="delete_alert"),
    path("api/alerts/<int:alert_id>/update/", update_alert, name="update_alert"),
    path("api/verify-email/<str:token>/", verify_email, name="verify_email"),

    # ⭐ THIS ONE RETURNS JSON (DATA)
    path("api/market-prices/recent/", get_dashboard_prices, name="get_dashboard_prices"),
    path("api/gov/market-prices/", gov_market_prices, name="gov_market_prices"),

   
]

