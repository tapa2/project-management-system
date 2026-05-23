from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=150, required=False, label="Ім'я")
    last_name = forms.CharField(max_length=150, required=False, label='Прізвище')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'avatar', 'position', 'bio')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
