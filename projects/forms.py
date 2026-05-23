from django import forms

from accounts.models import User

from .models import Project, ProjectMembership


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'description', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class MembershipForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(), label='Користувач')

    class Meta:
        model = ProjectMembership
        fields = ('user', 'role')

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if project is not None:
            existing = project.memberships.values_list('user_id', flat=True)
            self.fields['user'].queryset = User.objects.exclude(pk__in=existing).exclude(pk=project.owner_id)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.project is not None:
            instance.project = self.project
        if commit:
            instance.save()
        return instance
