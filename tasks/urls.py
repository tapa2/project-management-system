from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('new/in/<int:project_id>/', views.TaskCreateView.as_view(), name='create'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.TaskUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='delete'),
    path('<int:task_id>/comments/add/', views.CommentCreateView.as_view(), name='comment_create'),
]
