from django import forms
from .models import PatientProfile, Patient


class PatientProfileSetupForm(forms.ModelForm):
    """
    Allows a patient to set their birthday during profile setup.
    Birthday is NOT imported — it is user-entered here.
    """
    birthday = forms.DateField(
        required=False,
        label='Date of Birth',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        help_text='Used to compute your age in clinic records.',
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