from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from .models import User
from patients.models import Patient


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )


class UserCreateForm(UserCreationForm):
    """Admin creates a staff user account."""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'role', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class UserEditForm(forms.ModelForm):
    """Admin edits an existing staff user."""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'role', 'phone', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class PatientBulkUploadForm(forms.Form):
    """Upload an Excel file to bulk-create Patient records."""
    file = forms.FileField(
        label='Upload Excel File (.xlsx)',
        help_text=(
            'Required columns: id, first_name, last_name, sex. '
            'Optional: middle_name, college (abbreviation).'
        ),
        widget=forms.FileInput(attrs={
            'accept': '.xlsx',
            'class': 'form-control',
        })
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.xlsx'):
            raise forms.ValidationError('Please upload a valid Excel (.xlsx) file.')
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError('File size must be less than 5MB.')
        return file


class StaffPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['old_password'].label = 'Current Password'
        self.fields['new_password1'].label = 'New Password'
        self.fields['new_password2'].label = 'Confirm New Password'





class UserProfileForm(forms.ModelForm):
    """Staff user edits their own profile info."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


from patients.models import Patient, PatientProfile


class PatientProfileEditForm(forms.ModelForm):
    """Patient edits their full profile + contact info."""
    phone = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    emergency_contact_name = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    emergency_contact_phone = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = PatientProfile
        fields = [
            'religion', 'civil_status', 'year_level',
            'height_cm', 'weight_kg',
            'hypertension', 'diabetes', 'asthma', 'cardiac_problems', 'arthritis',
            'other_conditions',
            'bcg', 'dpt', 'opv', 'hepatitis_b', 'measles', 'tt',
            'immunization_others',
            'current_medications', 'vices', 'previous_illnesses', 'previous_hospitalizations',
            'address',
        ]
        widgets = {
            'religion': forms.TextInput(attrs={'class': 'form-control'}),
            'civil_status': forms.Select(attrs={'class': 'form-control'}),
            'year_level': forms.TextInput(attrs={'class': 'form-control'}),
            'height_cm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'other_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'immunization_others': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'current_medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'vices': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'previous_illnesses': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'previous_hospitalizations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)
        if patient:
            self.fields['phone'].initial = patient.phone
            self.fields['email'].initial = patient.email
            self.fields['emergency_contact_name'].initial = patient.emergency_contact_name
            self.fields['emergency_contact_phone'].initial = patient.emergency_contact_phone
        # Set checkboxes
        for field in ['hypertension', 'diabetes', 'asthma', 'cardiac_problems', 'arthritis',
                       'bcg', 'dpt', 'opv', 'hepatitis_b', 'measles', 'tt']:
            self.fields[field].widget.attrs['class'] = 'form-check-input'


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email',
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        from .models import User
        if not User.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError('No active account found with this email.')
        return email


class PasswordResetForm(forms.Form):
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            self.add_error('new_password2', 'Passwords do not match.')
        return cleaned