from django import forms
from core.validators import normalize_phone
from .models import PatientProfile, Patient, AcademicYearSettings


class PatientSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={
            'class': 'search-input',
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
        phone = (self.cleaned_data.get('phone') or '').strip()
        if not phone:
            raise forms.ValidationError('Phone number is required.')
        return normalize_phone(phone)

    def clean_emergency_contact_phone(self):
        phone = (self.cleaned_data.get('emergency_contact_phone') or '').strip()
        return normalize_phone(phone) if phone else ''


# ─── ACADEMIC YEAR SETTINGS FORM ───────────────────────────────────────────────

class AcademicYearSettingsForm(forms.Form):
    """Admin configures the academic year end date and archive threshold."""
    academic_year_end = forms.DateField(
        label='Academic Year End Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    archive_after_months = forms.IntegerField(
        label='Archive After Months',
        min_value=1,
        max_value=24,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 24}),
    )