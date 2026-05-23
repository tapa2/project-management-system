from django import forms

from .models import Comment, Task


class TaskForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S'],
        label='Дедлайн',
    )

    class Meta:
        model = Task
        fields = (
            'title', 'description', 'assignee', 'status', 'priority',
            'deadline', 'labels',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'labels': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            from accounts.models import User
            self.fields['assignee'].queryset = User.objects.filter(
                pk__in=list(project.memberships.values_list('user_id', flat=True)) + [project.owner_id]
            ).distinct()


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ваш коментар...'}),
        }
        labels = {'text': ''}
