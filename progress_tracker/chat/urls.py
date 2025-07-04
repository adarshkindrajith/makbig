from django.urls import path
from . import views

urlpatterns = [
    
    path('chat/', views.chatroom_view, name='chatroom'),
    path('admin-panel/', views.owner_panel, name='admin_panel'),
    path('report/<int:msg_id>/', views.report_message, name='report'),
    path('delete/<int:msg_id>/', views.delete_message, name='delete'),
    
]
