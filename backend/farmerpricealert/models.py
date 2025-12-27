from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models


# ==========================
#  USER (AUTH)
# ==========================
class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        default="farmer"
    )

    def __str__(self):
        return self.username


# ==========================
#  USER PROFILE
# ==========================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    location_state = models.CharField(max_length=120, blank=True)
    location_district = models.CharField(max_length=120, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile - {self.user.username}"


# ==========================
#  CROPS
# ==========================
class Crop(models.Model):
    name = models.CharField(max_length=120, unique=True)
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


# ==========================
#  MARKETS / MANDIS
# ==========================
class Market(models.Model):
    name = models.CharField(max_length=150)
    state = models.CharField(max_length=120)
    district = models.CharField(max_length=120)

    def __str__(self):
        return f"{self.name} ({self.district}, {self.state})"


# ==========================
#  MARKET PRICES (Gov data)
# ==========================
class MarketPrice(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)

    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    modal_price = models.DecimalField(max_digits=10, decimal_places=2)

    arrival_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-arrival_date"]

    def __str__(self):
        return f"{self.crop.name} - {self.market.name} ({self.arrival_date})"


# ==========================
#  ALERT SUBSCRIPTIONS
# ==========================
class AlertSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)

    target_price = models.DecimalField(max_digits=10, decimal_places=2)

    STATUS_CHOICES = (
        ("active", "Active"),
        ("triggered", "Triggered"),
        ("disabled", "Disabled"),
    )

    status = models.CharField(max_length=20, default="active", choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.crop.name} @ {self.market.name}"


# ==========================
#  ALERT HISTORY
# ==========================
class AlertHistory(models.Model):
    subscription = models.ForeignKey(AlertSubscription, on_delete=models.CASCADE)
    price = models.ForeignKey(MarketPrice, on_delete=models.CASCADE)

    message = models.TextField()
    is_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert for {self.subscription.user.username}"

class SiteContent(models.Model):
    page_name = models.CharField(max_length=100, unique=True)

    title = models.CharField(max_length=200, blank=True)
    subtitle = models.CharField(max_length=300, blank=True)
    banner_image = models.ImageField(upload_to="banners/", blank=True, null=True)

    def __str__(self):
        return self.page_name

class DashboardImage(models.Model):
    key = models.CharField(max_length=100, unique=True)   # example: live_prices_banner
    image = models.ImageField(upload_to="dashboard/")

    def __str__(self):
        return self.key

