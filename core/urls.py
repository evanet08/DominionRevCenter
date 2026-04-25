"""
URL configuration for core app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # ── Pages ──
    path('login/', views.login_page, name='login'),
    path('administration/', views.administration_page, name='administration'),
    path('mouvement/', views.mouvement_page, name='mouvement'),
    path('situation/', views.situation_page, name='situation'),
    path('verify-email/', views.verify_email_page, name='verify_email'),

    # ── Auth API ──
    path('api/login/', views.api_login, name='api_login'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/me/', views.api_me, name='api_me'),
    path('api/send-verification/', views.api_send_verification, name='api_send_verification'),
    path('api/verify-email/', views.api_verify_email, name='api_verify_email'),

    # ── Users API ──
    path('api/users/', views.api_users, name='api_users'),
    path('api/users/<uuid:pk>/', views.api_user_detail, name='api_user_detail'),
    path('api/users-list/', views.api_users_list, name='api_users_list'),

    # ── Organization API ──
    path('api/directions/', views.api_directions, name='api_directions'),
    path('api/departments/', views.api_departments, name='api_departments'),
    path('api/subdepartments/', views.api_subdepartments, name='api_subdepartments'),

    # ── Equipment API ──
    path('api/equipment/', views.api_equipment, name='api_equipment'),
    path('api/equipment/<int:pk>/', views.api_equipment_detail, name='api_equipment_detail'),
    path('api/equipment-list/', views.api_equipment_list, name='api_equipment_list'),

    # ── Core Business ──
    path('api/movements/', views.api_movements, name='api_movements'),
    path('api/stock/', views.api_stock, name='api_stock'),
    path('api/loans/', views.api_loans, name='api_loans'),
    path('api/history/', views.api_history, name='api_history'),
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
]
