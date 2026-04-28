from django import forms
from .models import PatientProfile, Patient


class PatientFullProfileSetupForm(forms.ModelForm):
    """
    Mandatory first-login profile setup for patients.
    Collects birthday, blood type, allergies, conditions, and contact info.
    This form is FORCED — patient cannot skip it.
    """

    # ── Fields sourced from Patient model (contact) ──────────────────────────
    phone = forms.CharField(
        required=True,
        max_length=30,
        label='Phone Number *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 09171234567',
        }),
        help_text='Format: 09XXXXXXXXX or +63XXXXXXXXXX',
    )
    email = forms.EmailField(
        required=False,
        label='Email Address (optional)',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
        }),
    )
    emergency_contact_name = forms.CharField(
        required=True,
        max_length=200,
        label='Emergency Contact Name *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full name of emergency contact',
        }),
    )
    emergency_contact_phone = forms.CharField(
        required=True,
        max_length=30,
        label='Emergency Contact Phone *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 09181234567',
        }),
    )

    class Meta:
        model = PatientProfile
        fields = [
            'birthday',
            'address',
            'blood_type',
            'known_allergies',
            'existing_conditions',
        ]
        widgets = {
            'birthday': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Home address',
            }),
            'blood_type': forms.Select(attrs={'class': 'form-control'}),
            'known_allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'e.g. Penicillin, Aspirin, shellfish... (write "None" if none)',
            }),
            'existing_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'e.g. Diabetes, Hypertension... (write "None" if none)',
            }),
        }
        labels = {
            'birthday': 'Date of Birth *',
            'address': 'Home Address (optional)',
            'blood_type': 'Blood Type (optional)',
            'known_allergies': 'Known Allergies *',
            'existing_conditions': 'Existing Medical Conditions *',
        }

    def clean_birthday(self):
        birthday = self.cleaned_data.get('birthday')
        if not birthday:
            raise forms.ValidationError('Date of birth is required.')
        from django.utils import timezone
        today = timezone.now().date()
        if birthday >= today:
            raise forms.ValidationError('Date of birth must be in the past.')
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        if age > 120:
            raise forms.ValidationError('Please enter a valid date of birth.')
        return birthday

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError('Phone number is required.')
        import re
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        if not re.match(r'^\d{7,15}$', cleaned):
            raise forms.ValidationError('Enter a valid phone number (7–15 digits).')
        return phone

    def clean_emergency_contact_phone(self):
        phone = self.cleaned_data.get('emergency_contact_phone', '').strip()
        if not phone:
            raise forms.ValidationError('Emergency contact phone is required.')
        import re
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        if not re.match(r'^\d{7,15}$', cleaned):
            raise forms.ValidationError('Enter a valid phone number (7–15 digits).')
        return phone

    def clean_known_allergies(self):
        val = self.cleaned_data.get('known_allergies', '').strip()
        if not val:
            raise forms.ValidationError(
                'This field is required. Write "None" if you have no known allergies.'
            )
        return val

    def clean_existing_conditions(self):
        val = self.cleaned_data.get('existing_conditions', '').strip()
        if not val:
            raise forms.ValidationError(
                'This field is required. Write "None" if you have no existing conditions.'
            )
        return val


class PatientProfileSetupForm(forms.ModelForm):
    """Lightweight form — used by staff to update only birthday."""
    birthday = forms.DateField(
        required=False,
        label='Date of Birth',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        help_text='Used to compute the patient\'s age in clinic records.',
    )

    class Meta:
        model = PatientProfile
        fields = ['birthday']


class PatientSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, patient ID, college...',
            'autofocus': True,
        })
    )


class PatientContactForm(forms.ModelForm):
    """Form for editing patient contact and emergency contact information."""

    class Meta:
        model = Patient
        fields = [
            'phone',
            'email',
            'emergency_contact_name',
            'emergency_contact_phone',
        ]
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 09171234567',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional email address',
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact full name',
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 09181234567',
            }),
        }
        labels = {
            'phone': 'Phone Number *',
            'email': 'Email Address (optional)',
            'emergency_contact_name': 'Emergency Contact Name',
            'emergency_contact_phone': 'Emergency Contact Phone',
        }
        help_texts = {
            'phone': 'Format: 09XXXXXXXXX or +63XXXXXXXXXX',
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError('Phone number is required.')
        return phone

    def clean_emergency_contact_phone(self):
        phone = self.cleaned_data.get('emergency_contact_phone', '').strip()
        if phone:
            import re
            cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
            if not re.match(r'^\d{7,15}$', cleaned):
                raise forms.ValidationError('Enter a valid phone number (7–15 digits).')
        return phone