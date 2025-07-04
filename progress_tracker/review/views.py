from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import HelpRequest
from learning.models import Module, Task, StudentTask 
from django.contrib.auth.models import User




def review_dashboard(request):
    return render(request, 'review.html')  # Returns partial HTML


@csrf_exempt
def submit_help_request(request):
    if request.method == "POST":
        request_type = request.POST.get("type")
        message = request.POST.get("message", "")

        email = request.session.get('student_email')  # Get student email from session
        if not email:
            return JsonResponse({"status": "error", "message": "Student not authenticated"})

        try:
            user = User.objects.get(email=email)  # Get actual User object
        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "User not found"})

        HelpRequest.objects.create(
            student=user,
            request_type=request_type,
            message=message
        )
        return JsonResponse({"status": "success", "message": "Request submitted!"})

    return JsonResponse({"status": "error", "message": "Invalid request."})


