from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from .models import User, StudentProfile


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Username or Student ID',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
        })
    )


class UserCreateForm(UserCreationForm):
    """Used by admin to create new users."""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'role', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class UserEditForm(forms.ModelForm):
    """Used by admin to edit existing users."""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'role', 'phone', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class StudentBulkUploadForm(forms.Form):
    """Form for uploading Excel file with student data."""
    file = forms.FileField(
        label='Upload Excel File (.xlsx)',
        help_text='File should contain columns: student_id, first_name, last_name, age, gender. Optional: middle_name, college',
        widget=forms.FileInput(attrs={
            'accept': '.xlsx',
            'class': 'form-control',
        })
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.xlsx'):
            raise forms.ValidationError('Please upload a valid Excel (.xlsx) file.')
        if file.size > 5 * 1024 * 1024:  # 5MB limit
            raise forms.ValidationError('File size must be less than 5MB.')
        return file


class StudentPasswordChangeForm(PasswordChangeForm):
    """Password change form for students."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['old_password'].label = 'Current Password'
        self.fields['new_password1'].label = 'New Password'
        self.fields['new_password2'].label = 'Confirm New Password'