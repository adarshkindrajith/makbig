from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from review.models import HelpRequest
from learning.models import Module, Task, StudentTask, StudentCurrentModule
from app1.models import dbstudent1
from app1.models import dbteacher1 
from django.db.models import Count
from .models import Course
from django.http import JsonResponse



from django.contrib.auth import logout
from django.shortcuts import redirect
@user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='/app1/teacherlogin/')
def staff_dashboard_view(request):
    selected_course_name = request.GET.get('course', '').strip()
    search_query = request.GET.get('search', '').strip().lower()

    student_users = User.objects.filter(is_staff=False)
    students = []

    for student in student_users:
        try:
            student_profile = dbstudent1.objects.get(s_email=student.email)
        except dbstudent1.DoesNotExist:
            continue

        # Filter by course name (if selected)
        if selected_course_name and student_profile.course.name != selected_course_name:
            continue

        # Filter by search query (name, email, username)
        if search_query:
            full_name = f"{student.first_name} {student.last_name}".lower()
            if search_query not in student.username.lower() and \
               search_query not in student.email.lower() and \
               search_query not in full_name:
                continue

        student_module_obj = StudentCurrentModule.objects.filter(student=student).first()
        current_module = student_module_obj.module if student_module_obj else None

        if current_module:
            tasks = Task.objects.filter(module=current_module)
            total_tasks = tasks.count()
            completed_tasks = StudentTask.objects.filter(student=student, task__in=tasks, is_completed=True).count()
        else:
            total_tasks = 0
            completed_tasks = 0

        progress = int((completed_tasks / total_tasks) * 100) if total_tasks else 0

        if progress >= 75:
            status = "On Track"
        elif progress >= 40:
            status = "Needs Help"
        else:
            status = "Behind Schedule"

        students.append({
            'student': student,
            'current_module': current_module.name if current_module else "No Module",
            'current_module_week': current_module.week if current_module else None,
            'completed': completed_tasks,
            'total': total_tasks,
            'progress': progress,
            'status': status,
            'course': student_profile.course,
            'student_id': student_profile.s_id,
            'profile_picture': student_profile.s_profilepicture,
            'student_profile': student_profile,
        })



    help_requests = HelpRequest.objects.select_related('student', 'accepted_by').filter(is_handled=False).order_by('-created_at')
    
    handled_requests = HelpRequest.objects.select_related('student', 'accepted_by').filter(is_handled=True).order_by('-created_at')

    for request_obj in help_requests:
         try:
            request_obj.student_profile = dbstudent1.objects.get(s_email=request_obj.student.email)
         except dbstudent1.DoesNotExist:
            request_obj.student_profile = None

    for request_obj in handled_requests:
         try:
            request_obj.student_profile = dbstudent1.objects.get(s_email=request_obj.student.email)
         except dbstudent1.DoesNotExist:
            request_obj.student_profile = None


    return render(request, 'staff/staff.html', {
        'students': students,
        'all_courses': Course.objects.all(),
        'teacher': dbteacher1.objects.filter(t_email=request.user.username).first(),
        'help_requests': help_requests,
        'handled_requests': handled_requests,
        'urgent_count': HelpRequest.objects.filter(request_type='urgent_review', is_handled=False).count(),
        'doubt_count': HelpRequest.objects.filter(request_type='doubt_session', is_handled=False).count(),
        'report_count': HelpRequest.objects.filter(request_type='report_issue', is_handled=False).count(),
        'week_review_count': HelpRequest.objects.filter(request_type='week_review', is_handled=False).count(),
    })



def accept_help_request(request, request_id):
    help_request = get_object_or_404(HelpRequest, id=request_id)
    if not help_request.accepted_by:
        help_request.accepted_by = request.user
        help_request.is_handled=True
        help_request.save()
    return redirect('staff_dashboard')



def mark_request_handled(request, request_id):
    help_request = get_object_or_404(HelpRequest, id=request_id)
    if help_request.accepted_by is None or help_request.accepted_by == request.user:
        help_request.is_handled = True
        help_request.save()

        # Recalculate counts
        urgent_count = HelpRequest.objects.filter(request_type='urgent_review', is_handled=False).count()
        doubt_count = HelpRequest.objects.filter(request_type='doubt_session', is_handled=False).count()
        report_count = HelpRequest.objects.filter(request_type='report_issue', is_handled=False).count()
        week_review_count = HelpRequest.objects.filter(request_type='week_review', is_handled=False).count()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # modern is_ajax check
            return JsonResponse({
                'success': True,
                'urgent_count': urgent_count,
                'doubt_count': doubt_count,
                'report_count': report_count,
                'week_review_count': week_review_count,
            })

    return redirect('staff_dashboard')



def approve_next_week(request, student_id):
    student = get_object_or_404(User, id=student_id, is_staff=False)

    try:
        student_profile = dbstudent1.objects.get(s_email=student.email)
        course = student_profile.course
    except dbstudent1.DoesNotExist:
        messages.error(request, "Student profile or course not found.")
        return redirect('staff_dashboard')

    
    modules = list(Module.objects.filter(course=course).order_by('week'))
    student_module_obj, created = StudentCurrentModule.objects.get_or_create(student=student, course=course)

    if not student_module_obj.module:
        if modules:
            student_module_obj.module = modules[0]
            student_module_obj.save()
            messages.success(request, f"Assigned first module '{modules[0].name}' to {student.username}.")
        else:
            messages.error(request, "No modules found.")
        return redirect('staff_dashboard')

    current_module = student_module_obj.module
    tasks = Task.objects.filter(module=current_module)
    total_tasks = tasks.count()
    completed_tasks = StudentTask.objects.filter(student=student, task__in=tasks, is_completed=True).count()

    if completed_tasks < total_tasks:
        messages.error(request, f"{student.username} has not completed all tasks in '{current_module.name}' (completed {completed_tasks} of {total_tasks}).")
        return redirect('staff_dashboard')

    try:
        current_index = modules.index(current_module)
    except ValueError:
        messages.error(request, "Current module not found in module list.")
        return redirect('staff_dashboard')

    if current_index + 1 < len(modules):
        next_module = modules[current_index + 1]
        student_module_obj.module = next_module
        student_module_obj.save()
        messages.success(request, f"Moved {student.username} to next module: '{next_module.name}'.")
    else:
        messages.info(request, f"{student.username} is already on the final module.")

    return redirect('staff_dashboard')


def student_module_progress(request, student_id):
    student = get_object_or_404(User, id=student_id, is_staff=False)

    try:
        student_profile = dbstudent1.objects.get(s_email=student.email)
        course = student_profile.course
    except dbstudent1.DoesNotExist:
        messages.error(request, "Student profile or course not found.")
        return redirect('staff_dashboard')

    #  Get current module for the student
    current_module_obj = StudentCurrentModule.objects.filter(student=student, course=course).first()

    if not current_module_obj or not current_module_obj.module:
        messages.warning(request, "No current module assigned to this student.")
        return redirect('staff_dashboard')

    current_module = current_module_obj.module

    # Get only tasks from the current module
    tasks = Task.objects.filter(module=current_module)

    task_progress = []
    for task in tasks:
        is_completed = StudentTask.objects.filter(student=student, task=task, is_completed=True).exists()
        task_progress.append({
            'task_title': task.title,
            'completed': is_completed,
        })

    return render(request, 'staff/student_module_progress.html', {
        'student': student,
        'current_module': current_module,
        'task_progress': task_progress,
    })




def stafflogout(request):
    logout(request)
    return redirect('teacherlogin')  
