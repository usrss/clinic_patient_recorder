from django import forms
from .models import PatientProfile, Patient


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