from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import User
from .utils import calculate_graduation_year
from patients.models import Patient, PatientProfile
from colleges.models import College, Course


# ── Shared file validation helpers ──────────────────────────────────────

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_profile_picture(file):
    """Server-side validation for profile picture uploads."""
    if not file:
        return
    content_type = getattr(file, 'content_type', None) or ''
    if content_type not in ALLOWED_IMAGE_TYPES:
        name = getattr(file, 'name', '').lower()
        ext_ok = name.endswith(('.jpg', '.jpeg', '.png', '.webp'))
        if not ext_ok:
            raise ValidationError(
                'Unsupported file type. Allowed types: JPG, PNG, WebP.'
            )
    if file.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f'File size ({file.size // 1024} KB) exceeds the maximum allowed size '
            f'of {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)} MB.'
        )


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True,
            'autocomplete': 'username',
            'aria-describedby': 'login-username-error',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
            'aria-describedby': 'login-password-error',
        })
    )


class UserCreateForm(UserCreationForm):
    """Admin creates a staff user account."""

    profile_picture = forms.ImageField(
        required=False,
        label='Profile Picture',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/webp',
        }),
        validators=[validate_profile_picture],
    )
    force_password_change = forms.BooleanField(
        required=False,
        initial=True,
        label='Force password change on next login',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'role', 'phone', 'profile_picture', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class UserEditForm(forms.ModelForm):
    """Admin edits an existing staff user."""
    force_password_change = forms.BooleanField(
        required=False,
        label='Force password change on next login',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'role', 'phone', 'profile_picture', 'is_active']
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/webp',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['profile_picture'].required = False
        self.fields['profile_picture'].label = 'Profile Picture'
        # Pre-fill force_password_change from instance
        if self.instance and self.instance.pk:
            self.fields['force_password_change'].initial = self.instance.force_password_change

    def clean_profile_picture(self):
        file = self.cleaned_data.get('profile_picture')
        if file:
            validate_profile_picture(file)
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
    """
    Staff user edits their own profile info.

    FIX: 'profile_picture' is intentionally excluded from Meta.fields.
    The view handles image saving explicitly to avoid a race condition
    between form.save() and the remove_picture logic.
    """
    remove_picture = forms.BooleanField(
        required=False,
        label='Remove current picture',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    # Declared here so the widget renders in the template, but NOT in Meta.fields
    # so form.save() does not touch it — the view handles it manually.
    profile_picture = forms.ImageField(
        required=False,
        label='Profile Picture',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/webp',
        }),
        validators=[validate_profile_picture],
    )

    class Meta:
        model = User
        # FIX: 'profile_picture' removed — handled manually in the view
        fields = ['first_name', 'last_name', 'email', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ('remove_picture',):
                field.widget.attrs.setdefault('class', 'form-control')

    def clean_profile_picture(self):
        file = self.cleaned_data.get('profile_picture')
        if file:
            validate_profile_picture(file)
        return file


class PatientProfileEditForm(forms.ModelForm):
    """Patient edits their full profile + contact info."""

    # ── Extra fields that live on Patient, not PatientProfile ──
    phone = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    emergency_contact_name = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    emergency_contact_phone = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    # ── Profile picture (lives on Patient, handled manually in the view) ──
    profile_picture = forms.ImageField(
        required=False,
        label='Profile Picture',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/webp',
        }),
        validators=[validate_profile_picture],
    )
    remove_picture = forms.BooleanField(
        required=False,
        label='Remove current picture',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    # ── Student-only fields (live on Patient, handled manually in the view) ──
    birthday = forms.DateField(
        required=False,
        label='Birthday',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    college = forms.ModelChoiceField(
        queryset=College.objects.all().order_by('name'),
        required=False,
        label='College',
        empty_label='Select College',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        required=False,
        label='Course',
        empty_label='Select Course',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    department = forms.CharField(
        max_length=150, required=False,
        label='Department',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    position = forms.CharField(
        max_length=150, required=False,
        label='Position / Designation',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = PatientProfile
        fields = [
            'religion', 'civil_status', 'year_level',
            'height_cm', 'weight_kg',
            'hypertension', 'diabetes', 'asthma', 'cardiac_problems', 'arthritis',
            'other_conditions',
            'known_allergies',          # FIX: was missing — caused silent data loss
            'blood_type',
            'bcg', 'dpt', 'opv', 'hepatitis_b', 'measles', 'tt',
            'immunization_others',
            'current_medications', 'vices', 'previous_illnesses',
            'previous_hospitalizations',
            'address',
        ]
        widgets = {
            'religion': forms.TextInput(attrs={'class': 'form-control'}),
            'civil_status': forms.Select(attrs={'class': 'form-control'}),
            'year_level': forms.TextInput(attrs={'class': 'form-control'}),
            'height_cm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'blood_type': forms.Select(attrs={'class': 'form-control'}),
            'other_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'known_allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'immunization_others': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'current_medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'vices': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'previous_illnesses': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'previous_hospitalizations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)
        # Pre-fill Patient fields into form initials
        if patient:
            self.fields['phone'].initial = patient.phone
            self.fields['email'].initial = patient.email
            self.fields['emergency_contact_name'].initial = patient.emergency_contact_name
            self.fields['emergency_contact_phone'].initial = patient.emergency_contact_phone
            self.fields['birthday'].initial = patient.profile.birthday if hasattr(patient, 'profile') and patient.profile.birthday else None
            self.fields['college'].initial = patient.college
            self.fields['course'].initial = patient.course
            self.fields['department'].initial = patient.department
            self.fields['position'].initial = patient.position

        # Apply checkbox styling
        for name in ('hypertension', 'diabetes', 'asthma', 'cardiac_problems', 'arthritis',
                     'bcg', 'dpt', 'opv', 'hepatitis_b', 'measles', 'tt'):
            self.fields[name].widget.attrs['class'] = 'form-check-input'

        # Add range validators to height/weight
        self.fields['height_cm'].validators.append(MinValueValidator(50))
        self.fields['height_cm'].validators.append(MaxValueValidator(250))
        self.fields['weight_kg'].validators.append(MinValueValidator(10))
        self.fields['weight_kg'].validators.append(MaxValueValidator(300))

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if email:
            qs = User.objects.filter(email=email)
            if self.user and self.user.pk:
                qs = qs.exclude(pk=self.user.pk)
            if qs.exists():
                raise forms.ValidationError('This email is already registered to another account.')
        return email

    def clean_profile_picture(self):
        file = self.cleaned_data.get('profile_picture')
        if file:
            validate_profile_picture(file)
        return file


# ── PROFILE COMPLETION FORM (Walk-in patient first login) ────────────────

class ProfileCompletionForm(forms.Form):
    """
    2-step form for walk-in patients completing their profile on first login.
    Pre-fills name, sex, birthday from existing Patient record (readonly in template).
    """

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
    ]

    # ── Pre-filled fields (readonly in template) ──
    first_name = forms.CharField(max_length=150, required=True)
    middle_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=150, required=True)
    sex = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')], required=True)
    birthday = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), required=False
    )

    # ── Editable fields ──
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Role')
    phone = forms.CharField(max_length=30, required=False, label='Phone Number')
    email = forms.EmailField(required=True, label='Email Address')

    # ── Personal Info ──
    address = forms.CharField(max_length=300, required=False)
    blood_type = forms.ChoiceField(
        choices=[
            ('', '—'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
            ('Unknown', 'Unknown'),
        ],
        required=False,
    )
    religion = forms.CharField(max_length=100, required=False)
    civil_status = forms.ChoiceField(
        choices=[
            ('', '—'), ('Single', 'Single'), ('Married', 'Married'),
            ('Widowed', 'Widowed'), ('Separated', 'Separated'),
        ],
        required=False,
    )
    height_cm = forms.DecimalField(max_digits=5, decimal_places=1, required=False,
        validators=[MinValueValidator(50), MaxValueValidator(250)])
    weight_kg = forms.DecimalField(max_digits=5, decimal_places=1, required=False,
        validators=[MinValueValidator(10), MaxValueValidator(300)])

    # ── Profile Picture ──
    profile_picture = forms.ImageField(
        required=False,
        label='Profile Picture',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/webp',
        }),
        validators=[validate_profile_picture],
    )

    # College — required for student and faculty (enforced in clean())
    college = forms.ModelChoiceField(
        queryset=College.objects.all().order_by('name'),
        required=False,
        label='College',
        empty_label='Select College',
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        required=False,
        label='Course',
        empty_label='Select Course',
    )
    year_level = forms.ChoiceField(
        choices=[
            ('', ''), ('1st Year', '1st Year'), ('2nd Year', '2nd Year'),
            ('3rd Year', '3rd Year'), ('4th Year', '4th Year'),
        ],
        required=False,
        label='Year Level',
    )
    department = forms.CharField(max_length=200, required=False, label='Department')
    position = forms.CharField(max_length=200, required=False, label='Position / Designation')

    # ── Emergency Contact ──
    emergency_contact_name = forms.CharField(max_length=200, required=False)
    emergency_contact_phone = forms.CharField(max_length=30, required=False)

    # ── Medical History ──
    hypertension = forms.BooleanField(required=False)
    diabetes = forms.BooleanField(required=False)
    asthma = forms.BooleanField(required=False)
    cardiac_problems = forms.BooleanField(required=False)
    arthritis = forms.BooleanField(required=False)
    other_conditions = forms.CharField(
        max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )
    known_allergies = forms.CharField(
        max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )

    # ── Immunization ──
    bcg = forms.BooleanField(required=False)
    dpt = forms.BooleanField(required=False)
    opv = forms.BooleanField(required=False)
    hepatitis_b = forms.BooleanField(required=False)
    measles = forms.BooleanField(required=False)
    tt = forms.BooleanField(required=False)
    immunization_others = forms.CharField(
        max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )

    # ── Medical Background ──
    current_medications = forms.CharField(
        max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )
    vices = forms.CharField(
        max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )
    previous_illnesses = forms.CharField(
        max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )
    previous_hospitalizations = forms.CharField(
        max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if email:
            qs = User.objects.filter(email=email)
            if self.user and self.user.pk:
                qs = qs.exclude(pk=self.user.pk)
            if qs.exists():
                raise forms.ValidationError('This email is already registered to another account.')
        return email

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role')

        # College required for student and faculty
        college = cleaned.get('college')
        if role in ('student', 'faculty') and not college:
            self.add_error('college', 'Please select your college.')

        # Course required for students
        if role == 'student' and not cleaned.get('course'):
            self.add_error('course', 'Please select your course.')

        # Year level required for students
        year = cleaned.get('year_level')
        if role == 'student' and not year:
            self.add_error('year_level', 'Year level is required for students.')

        # Department required for faculty and staff
        department = cleaned.get('department')
        if role in ('faculty', 'staff') and not department:
            self.add_error('department', 'Please enter your department.')

        # Calculate expected graduation year
        if role == 'student' and year:
            cleaned['_expected_graduation_year'] = calculate_graduation_year(year)
        else:
            cleaned['_expected_graduation_year'] = None

        # Clear irrelevant fields to avoid stale data
        if role == 'staff':
            cleaned['college'] = None
            cleaned['course'] = None
            cleaned['year_level'] = ''
        if role == 'student':
            cleaned['department'] = ''
            cleaned['position'] = ''

        return cleaned


class PasswordResetRequestForm(forms.Form):
    patient_id = forms.CharField(
        label='ID Number',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Student / Employee ID',
            'aria-describedby': 'fp-id-error',
        }),
    )

    # No clean_patient_id validation — user existence is checked in the view
    # with a generic response to prevent user enumeration.


class PasswordResetForm(forms.Form):
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            'aria-describedby': 'reset-pw1-error reset-strength-text',
        }),
        validators=[password_validation.validate_password],
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            'aria-describedby': 'reset-pw2-error reset-pw-match-indicator',
        }),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            self.add_error('new_password2', 'Passwords do not match.')
        return cleaned


# ── REGISTRATION FORM ──────────────────────────────────────────────────────

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
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
        }),
        label='Password'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
        }),
        label='Confirm Password'
    )

    # ── Personal Info ──
    birthday = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    address = forms.CharField(max_length=300, required=False)
    blood_type = forms.ChoiceField(
        choices=[
            ('', '—'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
            ('Unknown', 'Unknown'),
        ],
        required=False,
    )
    religion = forms.CharField(max_length=100, required=False)
    civil_status = forms.ChoiceField(
        choices=[
            ('', '—'), ('Single', 'Single'), ('Married', 'Married'),
            ('Widowed', 'Widowed'), ('Separated', 'Separated'),
        ],
        required=False,
    )
    height_cm = forms.DecimalField(max_digits=5, decimal_places=1, required=False,
        validators=[MinValueValidator(50), MaxValueValidator(250)])
    weight_kg = forms.DecimalField(max_digits=5, decimal_places=1, required=False,
        validators=[MinValueValidator(10), MaxValueValidator(300)])

    # College — required for student and faculty, optional for staff
    college = forms.ModelChoiceField(
        queryset=College.objects.all().order_by('name'),
        required=True,   # enforced conditionally in clean()
        label='College',
        empty_label='Select College',
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        required=False,
        label='Course',
        empty_label='Select Course',
    )
    year_level = forms.ChoiceField(
        choices=[
            ('', ''), ('1st Year', '1st Year'), ('2nd Year', '2nd Year'),
            ('3rd Year', '3rd Year'), ('4th Year', '4th Year'),
        ],
        required=True,
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
    other_conditions = forms.CharField(
        max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )
    known_allergies = forms.CharField(
        max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )

    # ── Immunization ──
    bcg = forms.BooleanField(required=False)
    dpt = forms.BooleanField(required=False)
    opv = forms.BooleanField(required=False)
    hepatitis_b = forms.BooleanField(required=False)
    measles = forms.BooleanField(required=False)
    tt = forms.BooleanField(required=False)
    immunization_others = forms.CharField(
        max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )

    # ── Medical Background ──
    current_medications = forms.CharField(
        max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )
    vices = forms.CharField(
        max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )
    previous_illnesses = forms.CharField(
        max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )
    previous_hospitalizations = forms.CharField(
        max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 2})
    )

    def clean_patient_id(self):
        patient_id = self.cleaned_data['patient_id']
        # Check if a Patient record exists (archived or active).
        # Deleted patients have no Patient record, allowing re-registration.
        if Patient.objects.filter(patient_id=patient_id).exists():
            raise forms.ValidationError('An account with this ID already exists.')
        return patient_id

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            password_validation.validate_password(password)
        return password

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

        # Course required for students
        if role == 'student' and not cleaned.get('course'):
            self.add_error('course', 'Please select your course.')

        # Year level required for students
        year = cleaned.get('year_level')
        if role == 'student' and not year:
            self.add_error('year_level', 'Year level is required for students.')

        # Department required for faculty and staff
        department = cleaned.get('department')
        if role in ('faculty', 'staff') and not department:
            self.add_error('department', 'Please enter your department.')

        # Calculate expected graduation year
        if role == 'student' and year:
            cleaned['_expected_graduation_year'] = calculate_graduation_year(year)
        else:
            cleaned['_expected_graduation_year'] = None

        # Clear irrelevant fields to avoid stale data
        if role == 'staff':
            cleaned['college'] = None
            cleaned['course'] = None
            cleaned['year_level'] = ''
        if role == 'student':
            cleaned['department'] = ''
            cleaned['position'] = ''

        return cleaned