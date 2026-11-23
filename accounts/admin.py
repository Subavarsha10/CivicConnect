
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        ('CivicConnect Information', {
            'fields': ('role', 'phone_number', 'address')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('CivicConnect Information', {
            'fields': ('role', 'phone_number', 'address')
        }),
    )

    list_display = (
        'username',
        'email',
        'role',
        'is_staff',
        'is_active'
    )

    list_filter = ('role', 'is_staff', 'is_active')

