from django.contrib import admin
from .models import dbstudent1
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django import forms
from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import dbteacher1, dbstudent1
from django.contrib.auth.models import User
from .models import AdminProfile


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 's_profilepicture')



# ✅ 1. Define your action
@admin.action(description='Approve selected students')
def approve_students(modeladmin, request, queryset):
    updated = queryset.update(s_status='approved')
    messages.success(request, f"{updated} student(s) approved.")

# ✅ 2. Register the model once and add everything to one admin class
@admin.register(dbstudent1)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['s_email', 's_firstname', 's_lastname', 's_status']
    actions = [approve_students]

    def save_model(self, request, obj, form, change):
        if obj.s_status == 'approved' and not obj.s_password:
            password = get_random_string(10)
            obj.s_password = make_password(password)

            try:
                send_mail(
                    'Your Account Has Been Approved',
                    f'Your login credentials:\n\nEmail: {obj.s_email}\nPassword: {password}',
                    settings.DEFAULT_FROM_EMAIL,
                    [obj.s_email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email send failed: {e}")

        super().save_model(request, obj, form, change)

@admin.register(dbteacher1)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['t_email']

    def save_model(self, request, obj, form, change):
        # Save the teacher model first
        super().save_model(request, obj, form, change)

        # Sync with Django User model
        if not User.objects.filter(username=obj.t_email).exists():
            user = User.objects.create_user(
                username=obj.t_email,
                email=obj.t_email,
                password=obj.t_password
            )
            user.is_staff = True
            user.save()
 