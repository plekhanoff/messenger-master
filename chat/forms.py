from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

class UserProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, label='Имя пользователя')
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label='О себе')

    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Сохраняем имя пользователя
            profile.user.username = self.cleaned_data['username']
            profile.user.save()
            profile.save()
        return profile