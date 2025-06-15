from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label="Password",widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="Confirm Password",widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model= User
        fields = ['username', 'email', 'password1', 'password2']