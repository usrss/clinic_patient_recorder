from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from .models import User
from patients.models import Patient, PatientProfile
from colleges.models import College


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


# ── REGISTRATION FORM ─────────────────────────────────────────────────

class RegistrationForm(forms.Form):
    """Self-registration for students, faculty, and staff with full medical profile."""

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
    ]

    # ── Account Info ──
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Role')
    patient_id = forms.CharField(max_length=30, label='ID Number')
    first_name = forms.CharField(max_length=150)
    middle_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=150)
    sex = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput(), label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput(), label='Confirm Password')

    # ── Personal Info ──
    birthday = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    address = forms.CharField(max_length=300, required=False)
    blood_type = forms.ChoiceField(
        choices=[('', '—'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
                 ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'), ('Unknown', 'Unknown')],
        required=False
    )
    religion = forms.CharField(max_length=100, required=False)
    civil_status = forms.ChoiceField(
        choices=[('', '—'), ('Single', 'Single'), ('Married', 'Married'),
                 ('Widowed', 'Widowed'), ('Separated', 'Separated')],
        required=False
    )
    height_cm = forms.DecimalField(max_digits=5, decimal_places=1, required=False)
    weight_kg = forms.DecimalField(max_digits=5, decimal_places=1, required=False)

    # College — required for student and faculty, optional for staff
    college = forms.ModelChoiceField(
        queryset=College.objects.all().order_by('name'),
        required=False,  # enforced conditionally in clean()
        label='College',
        empty_label='— Select College —',
    )
    year_level = forms.ChoiceField(
        choices=[('', '—'), ('1st Year', '1st Year'), ('2nd Year', '2nd Year'),
                 ('3rd Year', '3rd Year'), ('4th Year', '4th Year'), ('5th Year', '5th Year')],
        required=False,
        label='Year Level',
    )

    # Department — required for faculty and staff, hidden for students
    department = forms.CharField(max_length=200, required=False, label='Department')
    position = forms.CharField(max_length=200, required=False, label='Position / Designation')

    # ── Contact & Emergency ──
    phone = forms.CharField(max_length=30)
    emergency_contact_name = forms.CharField(max_length=200)
    emergency_contact_phone = forms.CharField(max_length=30)

    # ── Medical History ──
    hypertension = forms.BooleanField(required=False)
    diabetes = forms.BooleanField(required=False)
    asthma = forms.BooleanField(required=False)
    cardiac_problems = forms.BooleanField(required=False)
    arthritis = forms.BooleanField(required=False)
    other_conditions = forms.CharField(max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2}))
    known_allergies = forms.CharField(max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2}))

    # ── Immunization ──
    bcg = forms.BooleanField(required=False)
    dpt = forms.BooleanField(required=False)
    opv = forms.BooleanField(required=False)
    hepatitis_b = forms.BooleanField(required=False)
    measles = forms.BooleanField(required=False)
    tt = forms.BooleanField(required=False)
    immunization_others = forms.CharField(max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2}))

    # ── Medical Background ──
    current_medications = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 2}))
    vices = forms.CharField(max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2}))
    previous_illnesses = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 2}))
    previous_hospitalizations = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 2}))

    def clean_patient_id(self):
        patient_id = self.cleaned_data['patient_id']
        if User.objects.filter(username=patient_id).exists():
            raise forms.ValidationError('An account with this ID already exists.')
        return patient_id

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        role = cleaned.get('role')

        # Password match
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')

        # College required for student and faculty
        college = cleaned.get('college')
        if role in ('student', 'faculty') and not college:
            self.add_error('college', 'Please select your college.')

        # Year level required for students
        year = cleaned.get('year_level')
        if role == 'student' and not year:
            self.add_error('year_level', 'Year level is required for students.')

        # Department required for faculty and staff
        department = cleaned.get('department')
        if role in ('faculty', 'staff') and not department:
            self.add_error('department', 'Please enter your department.')

        # Clear college/year for staff; clear department for students
        if role == 'staff':
            cleaned['college'] = None
            cleaned['year_level'] = ''
        if role == 'student':
            cleaned['department'] = ''
            cleaned['position'] = ''

        return cleaned