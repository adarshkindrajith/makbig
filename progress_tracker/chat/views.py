from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from app1.models import dbstudent1
from .models import Message




def chatroom_view(request):
    student = None  # Default to None
    # Allow both superuser and approved students based on session
    if not request.user.is_authenticated:
        student_email = request.session.get('student_email')
        if not student_email:
            return redirect('studentlogin')
        try:
            student = dbstudent1.objects.get(s_email=student_email, s_status='approved')
        except dbstudent1.DoesNotExist:
            return redirect('studentlogin')
    else:
        # For logged-in users, if student record exists (depends on your logic)
        try:
            student = dbstudent1.objects.get(s_email=request.user.email, s_status='approved')
        except dbstudent1.DoesNotExist:
            student = None  # Optional, but safe

    messages = Message.objects.select_related('student', 'superuser','superuser__adminprofile', 'replied_to__student', 'replied_to__superuser').order_by('timestamp')
    reported_msgs = Message.objects.filter(reported=True).select_related('student', 'superuser').order_by('-timestamp')

    context = {
        'messages': messages,
        'reported_msgs': reported_msgs,
        'student': student,
        'user': request.user,
    }
    return render(request, 'chat/chatroom.html', context)





@login_required
def owner_panel(request):
    if not request.user.is_superuser:
        return redirect('chatroom')

    students = dbstudent1.objects.all()
    reported_msgs = Message.objects.filter(reported=True).select_related('student', 'superuser').order_by('-timestamp')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        badge = request.FILES.get('badge', None)
        try:
            student = dbstudent1.objects.get(id=student_id)
            student.badge = badge
            student.save()
        except dbstudent1.DoesNotExist:
            pass

        return redirect('owner_panel')

    return render(request, 'chat/admin-chat.html', {
        'students': students,
        'reported_msgs': reported_msgs,
        'messages': Message.objects.select_related('student', 'superuser').order_by('timestamp')
    })




@login_required
def report_message(request, msg_id):
    try:
        message = Message.objects.get(id=msg_id)
        message.reported = True
        message.save()
    except Message.DoesNotExist:
        pass
    return redirect("chatroom")


@login_required
def delete_message(request, msg_id):
    try:
        message = Message.objects.get(id=msg_id)
        sender = message.student or message.superuser

        # Allow superuser to delete or sender themselves
        if request.user.is_superuser or request.user == sender:
            message.delete()
    except Message.DoesNotExist:
        pass
    return redirect('chatroom')
