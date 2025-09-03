from django.contrib import admin
from .models import Province,District,Municipality

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, ManpowerProfile

class UserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ('phone_number', 'full_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('phone_number', 'full_name')
    ordering = ('phone_number',)

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        # ('Personal Info', {'fields': ('full_name', 'phone_number', 'username')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )


class UsersAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'full_name', 'is_staff', 'is_active')
    search_fields = ('phone_number', 'full_name')
    list_filter = ('is_staff', 'is_active')

class ManpowerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_full_name', 'phone_number', 'skill', 'province', 'district', 'municipality', 'ward', 'experience', 'rate', 'profile_picture')
    search_fields = ('user__full_name', 'skill', 'province__name', 'district__name', 'municipality__name')
    list_filter = ('province', 'district', 'municipality')
    # list_editable = ('profile_picture')

    def get_full_name(self, obj):
        return obj.user.full_name
    get_full_name.short_description = 'Full Name'

    def phone_number(self, obj):
        return obj.user.phone_number
    phone_number.short_description = 'Phone Number'


admin.site.register(CustomUser, UserAdmin)
admin.site.register(ManpowerProfile, ManpowerProfileAdmin)

admin.site.register(Province)
admin.site.register(District)
admin.site.register(Municipality)
# admin.site.register(Ward)
# admin.site.register(ManpowerProfile)
