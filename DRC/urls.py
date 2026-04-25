"""
DRC URL Configuration.
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda r: redirect('/login/')),
    path('', include('core.urls')),
]
