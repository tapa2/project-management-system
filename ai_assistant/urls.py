from django.urls import path

from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('request-description/', views.request_description, name='request_description'),
    path('suggestions/<int:pk>/', views.suggestion_status, name='suggestion_status'),
]
