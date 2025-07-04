from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib.auth.hashers import check_password, make_password
import random,string
from .models import dbstudent1, dbteacher1
from .forms import studentregistrationform, teacherloginform
from django.conf import settings
from django.core.mail import send_mail
from .forms import studentregistrationform  
from .models import dbstudent1  
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login,logout




def home(request):
    return render(request, "home.html")


def addteachers(request):
    from django.contrib.auth.models import User

    emails = [
        "teacher2@gmail.com",
        "teacher3@gmail.com",
        "teacher4@gmail.com",
        "teacher5@gmail.com",
    ]
    passwords = [
        "23451",
        "34512",
        "45123",
        "51234",
    ]

    for email, password in zip(emails, passwords):
        user, created = User.objects.get_or_create(username=email, email=email)
        if created:
            user.set_password(password)
            user.is_staff = True
            user.save()
            print(f"Created staff user: {email}")
        else:
            print(f"User already exists: {email}")


def teacherlogin(request):
    form = teacherloginform(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['t_email']
            password = form.cleaned_data['t_password']

            # Authenticate user using Django auth
            user = authenticate(request, username=email, password=password)

            if user is not None:
                if user.is_staff:
                    login(request, user)  # Log the user in
                    return redirect('staff_dashboard')
                else:
                    messages.error(request, 'You do not have staff permissions.')
            else:
                messages.error(request, 'Invalid credentials.')
        else:
            messages.error(request, 'Please correct the form errors.')

    return render(request, "teacherlogin.html", {'form': form})



def teacherlogout(request):
    request.session.flush()
    return redirect('teacherlogin')




def student_register(request):
    if request.method == 'POST':
        form = studentregistrationform(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)

            raw_password = form.cleaned_data.get('s_password')  # 🔐 Get raw password before hashing
            student.save()  # Will hash password inside `dbstudent1.save()`

            # ✅ Create matching Django User
            if not User.objects.filter(email=student.s_email).exists():
                User.objects.create_user(
                    username=student.s_email,  # Using email as username
                    email=student.s_email,
                    password=raw_password
                )

            # ✅ Notify Admin
            send_mail(
                'New student registration',
                f'Student {student.s_firstname} {student.s_lastname} has registered. Please review their details.',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            return render(request, "registrationsuccess.html")
    else:
        form = studentregistrationform()

    return render(request, "register.html", {'form': form})



def studentlogin(request):
    if request.method == 'POST':
        email = request.POST.get('s_email', '').strip()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            messages.error(request, "Both email and password are required.")
            return render(request, "studentlogin.html")

        # ✅ First check if superuser is trying to log in
        user = authenticate(request, username=email, password=password)
        if user and user.is_superuser:
            login(request, user)
            return redirect('admin_panel')  # Assuming 'owner_panel' points to admin-chat

        try:
            student = dbstudent1.objects.get(s_email=email)
            if student.s_status != 'approved':
                messages.error(request, "Your account has not been approved yet.")
                return render(request, "studentlogin.html")

            if check_password(password, student.s_password):
                user, created = User.objects.get_or_create(
                    username=student.s_email,
                    defaults={
                        'email': student.s_email,
                        'first_name': student.s_firstname,
                        'last_name': student.s_lastname,
                    }
                )

                if created:
                    user.set_password(password)
                    user.save()

                if not student.user:
                    student.user = user
                    student.save()

                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                request.session['student_email'] = student.s_email

                return redirect('student_dashboard')
            else:
                messages.error(request, "Invalid email or password.")

        except dbstudent1.DoesNotExist:
            messages.error(request, "Invalid email or password.")

    return render(request, "studentlogin.html")


def studentlogout(request):
    request.session.flush()
    return redirect('studentlogin')






@require_POST
@transaction.atomic
def approve_student(request, student_id):
    student = get_object_or_404(dbstudent1, pk=student_id)

    if student.s_status == 'approved' and student.s_password:
        messages.info(request, f"Student {student.s_email} is already approved.")
        return redirect('custom_admin_dashboard')

    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    student.s_status = 'approved'
    student.s_password = make_password(password)
    student.save()

    # Ensure User exists
    user, created = User.objects.get_or_create(
        username=student.s_email,
        defaults={
            'email': student.s_email,
            'first_name': student.s_firstname,
            'last_name': student.s_lastname
        }
    )
    user.set_password(password)
    user.save()

    student.user = user
    student.save()

    try:
        send_mail(
            'Your Account Has Been Approved',
            f'Your login credentials:\n\nEmail: {student.s_email}\nPassword: {password}',
            settings.DEFAULT_FROM_EMAIL,
            [student.s_email],
            fail_silently=False,
        )
        messages.success(request, f"Student {student.s_email} approved and credentials sent.")
    except Exception as e:
        messages.error(request, f"Email sending failed: {e}")

    return redirect('custom_admin_dashboard')
