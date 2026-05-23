from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import MembershipForm, ProjectForm
from .models import Project, ProjectMembership


class ProjectAccessMixin(LoginRequiredMixin):
    """Проєкт доступний власнику або учасникам."""

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct()


class ProjectOwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Лише власник може редагувати/видаляти проєкт."""

    def test_func(self):
        project = self.get_object()
        return project.owner_id == self.request.user.id


class ProjectListView(ProjectAccessMixin, ListView):
    model = Project
    template_name = 'projects/list.html'
    context_object_name = 'projects'
    paginate_by = 12


class ProjectDetailView(ProjectAccessMixin, DetailView):
    model = Project
    template_name = 'projects/detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['memberships'] = self.object.memberships.select_related('user')
        ctx['tasks'] = self.object.tasks.select_related('assignee').all()
        ctx['is_owner'] = self.object.owner_id == self.request.user.id
        return ctx


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        ProjectMembership.objects.create(
            project=self.object,
            user=self.request.user,
            role=ProjectMembership.Role.OWNER,
        )
        messages.success(self.request, 'Проєкт створено.')
        return response

    def get_success_url(self):
        return reverse_lazy('projects:detail', args=[self.object.pk])


class ProjectUpdateView(ProjectOwnerRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'

    def get_success_url(self):
        return reverse_lazy('projects:detail', args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, 'Проєкт оновлено.')
        return super().form_valid(form)


class ProjectDeleteView(ProjectOwnerRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/confirm_delete.html'
    success_url = reverse_lazy('projects:list')

    def form_valid(self, form):
        messages.success(self.request, 'Проєкт видалено.')
        return super().form_valid(form)


class AddMemberView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = MembershipForm
    template_name = 'projects/add_member.html'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs['project_id'])
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.project.owner_id == self.request.user.id

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['project'] = self.project
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Учасника додано.')
        return redirect('projects:detail', pk=self.project.pk)


class RemoveMemberView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ProjectMembership
    template_name = 'projects/confirm_remove_member.html'

    def test_func(self):
        membership = self.get_object()
        return (
            membership.project.owner_id == self.request.user.id
            and membership.user_id != membership.project.owner_id
        )

    def get_success_url(self):
        return reverse_lazy('projects:detail', args=[self.object.project_id])

    def form_valid(self, form):
        messages.success(self.request, 'Учасника видалено.')
        return super().form_valid(form)
