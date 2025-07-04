from django.urls import path
from . import views

urlpatterns = [
    path('ajax-review/', views.review_dashboard, name='review_dashboard'),
    path('submit-help/', views.submit_help_request, name='submit_help'),
]
