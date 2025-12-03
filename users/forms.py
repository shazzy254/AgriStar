from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile

class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=User.Role.choices, 
        required=True,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        help_text='Select your role to get a personalized dashboard'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter a strong password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm your password'})

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'phone_number', 'whatsapp_number', 'avatar', 'farm_size', 'main_crops', 'company_name']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +254...'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +254...'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'farm_size': forms.TextInput(attrs={'class': 'form-control'}),
            'main_crops': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone_number')
        whatsapp = cleaned_data.get('whatsapp_number')
        role = self.instance.user.role

        if role == 'FARMER' and not phone and not whatsapp:
            raise forms.ValidationError("Farmers must provide at least one contact method (Phone or WhatsApp).")
        return cleaned_data

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'language_preference']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'language_preference': forms.Select(attrs={'class': 'form-select'}),
        }
