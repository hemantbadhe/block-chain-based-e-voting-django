from django.contrib import admin
from django.apps import apps
from django.contrib.auth.admin import UserAdmin

from simulation.models import User


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password',)}),
        (('Personal info'),
         {'fields': ('first_name', 'last_name', 'email', 'is_active', 'public_key')}),

    )
    list_display = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')


admin.site.register(User, CustomUserAdmin)
