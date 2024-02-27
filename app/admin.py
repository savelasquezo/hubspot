from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

import app.models as models

class MyAdminSite(admin.AdminSite):
    index_title = 'Hubspot'
    verbose_name = "Hubspot"

admin_site = MyAdminSite()
admin.site = admin_site
admin_site.site_header = "Hubspot"

class AccountAdmin(BaseUserAdmin):
    list_display = ('username', 'email','first_name','last_name','date_joined')
    search_fields = ('username', 'email')

    fieldsets = (
        (None, {'fields': (('username''is_active','is_staff'), 'password')}),
            ('', {'fields': (
            ('email','date_joined'),
            ('first_name','last_name'),
        )}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    list_filter=['is_active','is_staff']

    def get_readonly_fields(self, request, obj=None):
        return ['username','email','date_joined']
    
admin.site.register(models.Account, AccountAdmin)