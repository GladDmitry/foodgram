from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Subscription, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка пользователей."""

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
    )
    list_editable = ('is_staff',)
    list_filter = ('username', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Персональная информация', {'fields': (
            'first_name',
            'last_name',
            'avatar'
        )}),
        ('Разрешения', {'fields': ('is_staff', 'is_active')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'first_name',
                'last_name',
                'password1',
                'password2'
            ),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка подписок."""

    list_display = ('id', 'user', 'author')
    list_editable = ('user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user__username', 'author__username')


admin.site.empty_value_display = 'Не задано'
