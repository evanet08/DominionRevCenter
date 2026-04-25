from django.contrib import admin
from .models import User, Direction, Department, SubDepartment, Equipment, Movement


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'role', 'email_verified', 'is_active', 'created_at']
    list_filter = ['role', 'email_verified', 'is_active']
    search_fields = ['name', 'email']


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'direction', 'code', 'created_at']
    list_filter = ['direction']


@admin.register(SubDepartment)
class SubDepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'code', 'created_at']
    list_filter = ['department']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'model', 'internal_id', 'serial_number', 'condition']
    list_filter = ['condition']
    search_fields = ['name', 'internal_id', 'serial_number']


@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'action_type', 'quantity', 'completed_by', 'assigned_to', 'date']
    list_filter = ['action_type', 'date']
    search_fields = ['equipment__name']
