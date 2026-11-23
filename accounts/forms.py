
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CitizenRegistrationForm(UserCreationForm):

    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'address',
            'password1',
            'password2',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'citizen'

        if commit:
            user.save()

        return user
