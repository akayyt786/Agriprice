from django.urls import path
from .views import RegisterView
from django.urls import path
from .views import registration_page

from .views import dashboard_page
from .views import (
    login_page,
    RegisterView,
    CookieLoginView,
    gov_market_prices,
    market_prices_page,
)




urlpatterns = [
    path("", login_page, name="login_root"),
    path("register/", registration_page, name="register_page"),
    path("login/", login_page, name="login_page"),

    # APIs  ❗ JSON ENDPOINT
    path("api/register/", RegisterView.as_view(), name="register_api"),
    path("api/login-cookie/", CookieLoginView.as_view(), name="cookie_login"),

    # ⭐ THIS ONE RETURNS JSON (DATA)
    path("api/gov/market-prices/", gov_market_prices, name="gov_market_prices"),

    path("dashboard/", dashboard_page, name="dashboard"),

    # ⭐ THIS ONE RETURNS HTML PAGE (YOUR UI)
    path("market-prices/", market_prices_page, name="market_prices_page"),
]

