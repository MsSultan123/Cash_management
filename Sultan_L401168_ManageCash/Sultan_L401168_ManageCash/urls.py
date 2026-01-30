"""
URL configuration for Sultan_L401168_ManageCash project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ManageCash.urls')),
]