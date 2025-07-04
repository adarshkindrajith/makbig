from django.urls import path
from . import views



urlpatterns = [
    path('student_register/', views.student_register, name="student_register"),

    # Approve student with student_id (POST)
    path('approve-student/<int:student_id>/', views.approve_student, name='approve_student'),

    # Student login
    path('login/', views.studentlogin, name='studentlogin'),
    path('studentlogout/', views.studentlogout, name='student_logout'),

    # Teacher login/logout and dashboard
    path('teacherlogin/', views.teacherlogin, name="teacherlogin"),
    
   
    path('addteachers/', views.addteachers, name="addteachers"),
    path('teacherlogout/', views.teacherlogout, name="teacherlogout"),

    # Home page
    path('home/', views.home, name="home"),

    # Student logout and profile
    path('studentlogout/', views.studentlogout, name="studentlogout"),
    
]
