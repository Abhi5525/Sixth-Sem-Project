from django.contrib import admin
from .models import Province, District, Municipality, CustomUser, ManpowerProfile, Skill

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
            ('Personal Info', {'fields': ('full_name', 'email', 'is_client', 'is_professional')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', 'is_staff', 'is_active','is_client','is_professional', 'full_name', 'email'),
        }

        ),
    )


class UsersAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'full_name', 'is_staff', 'is_active', 'email', 'is_client', 'is_professional')
    search_fields = ('phone_number', 'full_name')
    list_filter = ('is_staff', 'is_active')

class ManpowerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_full_name', 'phone_number', 'get_skills', 'province', 'district', 'municipality', 'ward', 'experience', 'rate', 'profile_picture')
    search_fields = ('user__full_name', 'skill', 'skills__name', 'province', 'district', 'municipality')
    list_filter = ('province', 'district', 'municipality')
    filter_horizontal = ('skills',)  # Better UX for ManyToMany fields
    # list_editable = ('profile_picture')

    def get_full_name(self, obj):
        return obj.user.full_name
    get_full_name.short_description = 'Full Name'

    def phone_number(self, obj):
        return obj.user.phone_number
    phone_number.short_description = 'Phone Number'

    def get_skills(self, obj):
        return ", ".join([skill.name for skill in obj.skills.all()]) or obj.skill or "No skills"
    get_skills.short_description = 'Skills'


class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description')
    search_fields = ('name', 'category')
    list_filter = ('category',)


admin.site.register(CustomUser, UserAdmin)
admin.site.register(ManpowerProfile, ManpowerProfileAdmin)
admin.site.register(Skill, SkillAdmin)

admin.site.register(Province)
admin.site.register(District)
admin.site.register(Municipality)
# admin.site.register(Ward)
# admin.site.register(ManpowerProfile)
