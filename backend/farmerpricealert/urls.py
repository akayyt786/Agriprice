from django.urls import path
from .views import RegisterView
from django.urls import path
from .views import registration_page
from .views import dashboard_page
from .views import (
    login_page,
    RegisterView,
    CookieLoginView,
)



urlpatterns = [
    path("", login_page, name="login_root"),
    path("register/", registration_page, name="register_page"),
    path("login/", login_page, name="login_page"),

    # APIs
    path("api/register/", RegisterView.as_view(), name="register_api"),
    path("api/login-cookie/", CookieLoginView.as_view(), name="cookie_login"),
    path("dashboard/", dashboard_page, name="dashboard"),
]
