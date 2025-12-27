from django.urls import path
from .views import RegisterView
from django.urls import path
from .views import registration_page
from .views import dashboard_page



urlpatterns = [
    path("", RegisterView.as_view(), name="register"),
    path("register-page/", registration_page, name="registration_page"),
    path("dashboard/", dashboard_page, name="dashboard"),
]
