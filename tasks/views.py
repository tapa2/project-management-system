from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from projects.models import Project

from .forms import CommentForm, TaskForm
from .models import Task


def _user_has_project_access(user, project: Project) -> bool:
    return project.owner_id == user.id or project.memberships.filter(user_id=user.id).exists()


class TaskAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Доступ до задачі — лише власнику або учаснику її проєкту."""

    def test_func(self):
        task = self.get_object()
        return _user_has_project_access(self.request.user, task.project)


class TaskCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs['project_id'])
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return _user_has_project_access(self.request.user, self.project)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['project'] = self.project
        return ctx

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Задачу створено.')
        return response

    def get_success_url(self):
        return reverse_lazy('tasks:detail', args=[self.object.pk])


class TaskDetailView(TaskAccessMixin, DetailView):
    model = Task
    template_name = 'tasks/detail.html'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comments'] = self.object.comments.select_related('author')
        ctx['comment_form'] = CommentForm()
        ctx['attachments'] = self.object.attachments.select_related('uploaded_by')
        ctx['can_edit'] = _user_has_project_access(self.request.user, self.object.project)
        return ctx


class TaskUpdateView(TaskAccessMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.object.project
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['project'] = self.object.project
        return ctx

    def get_success_url(self):
        return reverse_lazy('tasks:detail', args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, 'Задачу оновлено.')
        return super().form_valid(form)


class TaskDeleteView(TaskAccessMixin, DeleteView):
    model = Task
    template_name = 'tasks/confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('projects:detail', args=[self.object.project_id])

    def form_valid(self, form):
        messages.success(self.request, 'Задачу видалено.')
        return super().form_valid(form)


class CommentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = CommentForm
    http_method_names = ['post']

    def dispatch(self, request, *args, **kwargs):
        self.task = get_object_or_404(Task.objects.select_related('project'), pk=kwargs['task_id'])
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return _user_has_project_access(self.request.user, self.task.project)

    def form_valid(self, form):
        form.instance.task = self.task
        form.instance.author = self.request.user
        form.save()
        messages.success(self.request, 'Коментар додано.')
        return redirect('tasks:detail', pk=self.task.pk)

    def form_invalid(self, form):
        messages.error(self.request, 'Коментар порожній.')
        return redirect('tasks:detail', pk=self.task.pk)
