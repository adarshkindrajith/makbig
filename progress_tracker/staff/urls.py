from django.urls import path
from . import views

urlpatterns = [
   
    path('', views.staff_dashboard_view, name='staff_dashboard'),  # Combined dashboard
    path('accept/<int:request_id>/', views.accept_help_request, name='accept_help_request'),
    path('handle/<int:request_id>/', views.mark_request_handled, name='mark_request_handled'),
    path('student/<int:student_id>/progress/', views.student_module_progress, name='student_module_progress'),
    path('approve-next/<int:student_id>/', views.approve_next_week, name='approve_next_week'),
    path('stafflogout/', views.stafflogout, name='staff_logout'), 
]
