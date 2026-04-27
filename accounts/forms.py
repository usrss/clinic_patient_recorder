from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from .models import User


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