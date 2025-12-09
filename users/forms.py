from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile, RiderProfile

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
        fields = ['bio', 'location', 'phone_number', 'whatsapp_number', 'avatar', 
                  'farm_size', 'main_crops', 'company_name', 
                  'buyer_type', 'business_name', 'marketplace_location']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City/Area'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +254...'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +254...'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'farm_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5 acres'}),
            'main_crops': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Maize, Beans'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your company name'}),
            'buyer_type': forms.Select(attrs={'class': 'form-select'}),
            'business_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your business/marketplace name'}),
            'marketplace_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Gikomba Market, Nairobi'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get user role from instance
        if self.instance and self.instance.user:
            role = self.instance.user.role
            
            # Remove fields not relevant to the user's role
            if role == 'FARMER':
                # Farmers only need: bio, location, phone, whatsapp, avatar, farm_size, main_crops
                self.fields.pop('company_name', None)
                self.fields.pop('buyer_type', None)
                self.fields.pop('business_name', None)
                self.fields.pop('marketplace_location', None)
            elif role == 'SUPPLIER':
                # Suppliers only need: bio, location, phone, whatsapp, avatar, company_name
                self.fields.pop('farm_size', None)
                self.fields.pop('main_crops', None)
                self.fields.pop('buyer_type', None)
                self.fields.pop('business_name', None)
                self.fields.pop('marketplace_location', None)
            elif role == 'BUYER':
                # Buyers only need: bio, location, phone, whatsapp, avatar, buyer_type, business_name, marketplace_location
                self.fields.pop('farm_size', None)
                self.fields.pop('main_crops', None)
                self.fields.pop('company_name', None)
            else:
                # For other roles, keep basic fields only
                self.fields.pop('farm_size', None)
                self.fields.pop('main_crops', None)
                self.fields.pop('company_name', None)
                self.fields.pop('buyer_type', None)
                self.fields.pop('business_name', None)
                self.fields.pop('marketplace_location', None)

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

# --- Registration Profile Forms ---

class FarmerRegistrationProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name', 'phone_number', 'whatsapp_number', 'location', 'address', 'farm_size', 'main_crops']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Farm Name (Optional)'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'WhatsApp Number'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City/Area (e.g. Nairobi, Nakuru)'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street Address'}),
            'farm_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5 Acres'}),
            'main_crops': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Maize, Beans'}),
        }

class SupplierRegistrationProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['company_name', 'phone_number', 'whatsapp_number', 'location', 'address']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'WhatsApp Number'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City/Area'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Shop Street Address'}),
        }

class BuyerRegistrationProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name', 'phone_number', 'location', 'address']
        widgets = {
             'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Display Name (Optional)'}),
             'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
             'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City/Area'}),
             'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Delivery Street Address'}),
        }

class RiderRegistrationProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name', 'phone_number', 'location', 'address']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Display Name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City/Area'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Home Street Address'}),
        }

class RiderProfileForm(forms.ModelForm):
    class Meta:
        model = RiderProfile
        fields = ['id_number', 'is_available', 'active_hours_start', 'active_hours_end']
        widgets = {
            'id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID'}),
            'active_hours_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'active_hours_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class RiderVehicleForm(forms.ModelForm):
    class Meta:
        model = RiderProfile
        fields = ['vehicle_type', 'vehicle_plate_number']
        widgets = {
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'vehicle_plate_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'KAA 123A'}),
        }
