from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from learning.models import Module, Task, StudentTask,StudentCurrentModule,StudentBadge,Badge
from app1.views import studentlogin as student_login
from app1.models import dbstudent1
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from app1.models import dbstudent1
from learning.models import Module, Task, StudentTask, StudentCurrentModule, StudentBadge, Badge
from django.http import JsonResponse

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from learning.models import StudentTask, Task

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from learning.models import StudentTask, Task



def student_dashboard(request):
    email = request.session.get('student_email')
    if not email:
        return redirect('studentlogin')

    try:
        student_profile = dbstudent1.objects.get(s_email=email)
    except dbstudent1.DoesNotExist:
        return redirect('studentlogin')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = None

    module = None
    task_statuses = []
    completed = 0
    total = 0
    progress = 0
    student_badges = []
    course = student_profile.course

    if user and course:
        # Get or create current module record for student & course
        student_module_obj, created = StudentCurrentModule.objects.get_or_create(student=user, course=course)

        # If no module set or course mismatch, assign first module of the course
        if not student_module_obj.module or student_module_obj.module.course != course:
            first_module = Module.objects.filter(course=course).order_by('week').first()
            student_module_obj.module = first_module
            student_module_obj.save()

        module = student_module_obj.module

        if module:
            tasks = module.tasks.all()
            for task in tasks:
                completed_status = StudentTask.objects.filter(student=user, task=task, is_completed=True).exists()
                task_statuses.append({
                    'task': task,
                    'is_completed': completed_status
                })

            completed = sum(1 for t in task_statuses if t['is_completed'])
            total = len(task_statuses)
            progress = (completed / total) * 100 if total else 0

            # Award all badges for current and previous weeks in this course
            badges_to_award = Badge.objects.filter(week__lte=module.week)
            for badge in badges_to_award:
                StudentBadge.objects.get_or_create(student=user, badge=badge)

            student_badges = StudentBadge.objects.filter(student=user).select_related('badge')

    context = {
        'student': student_profile,
        'user': user,
        's_email': email,
        'module': module,
        'task_statuses': task_statuses,
        'progress': int(progress),
        'completed': completed,
        'total': total,
        'student_badges': student_badges,
        'course': course,
    }

    return render(request, 'learning/student_dashboard.html', context)


@csrf_exempt
def complete_task(request, task_id):
    if request.method == 'POST':
        email = request.session.get('student_email')
        if not email:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'}, status=404)

        task = get_object_or_404(Task, id=task_id)

        # ✅ Ensure the task's module's course matches the student's course
        try:
            student_profile = dbstudent1.objects.get(s_email=email)
        except dbstudent1.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student profile not found'}, status=404)

        student_course = student_profile.course
        if task.module.course != student_course:
            return JsonResponse({'success': False, 'error': 'Access denied for this task'}, status=403)

        # Continue as before
        student_task, created = StudentTask.objects.get_or_create(
            student=user,
            task=task,
            defaults={'is_completed': True}
        )

        if not created:
            student_task.is_completed = not student_task.is_completed
            student_task.save()

        all_tasks = Task.objects.filter(module=task.module).count()
        completed_tasks = StudentTask.objects.filter(
            student=user,
            task__module=task.module,
            is_completed=True
        ).count()
        progress = int((completed_tasks / all_tasks) * 100) if all_tasks else 0

        return JsonResponse({
            'success': True,
            'is_completed': student_task.is_completed,
            'progress': progress,
            'completed': completed_tasks,
            'total': all_tasks
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def submit_review(request):
    if request.method == 'POST':
        return redirect('student_dashboard')
    return redirect('student_dashboard')



from django.contrib.auth import logout
from django.shortcuts import redirect

def studentlogout(request):
    logout(request)
    return redirect('studentlogin')  # Redirects to login.html
def module_view(request):
    email = request.session.get('student_email')
    if not email:
        return redirect('studentlogin')

    try:
        student_profile = dbstudent1.objects.get(s_email=email)
        user = User.objects.get(email=email)
    except (dbstudent1.DoesNotExist, User.DoesNotExist):
        return redirect('studentlogin')

    course = student_profile.course
    student_module_obj, created = StudentCurrentModule.objects.get_or_create(student=user, course=course)

    # Assign module if missing or mismatched
    if not student_module_obj.module or student_module_obj.module.course != course:
        first_module = Module.objects.filter(course=course).order_by('week').first()
        student_module_obj.module = first_module
        student_module_obj.save()

    module = student_module_obj.module

    context = {
        'module': module
    }

    return render(request, 'learning/module.html', context)

from review.models import HelpRequest  # adjust this to your actual model name

def chat_home(request):
    help_requests = HelpRequest.objects.all()  # or filter by user if needed
    return render(request, 'learning/chat_home.html', {'help_requests': help_requests})

