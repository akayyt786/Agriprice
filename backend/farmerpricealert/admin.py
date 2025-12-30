from django.contrib import admin
from .models import SiteContent, DashboardImage
from .models import User

admin.site.register(User)
admin.site.register(SiteContent)
admin.site.register(DashboardImage)
