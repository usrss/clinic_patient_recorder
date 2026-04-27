from django import forms
from django.forms import formset_factory

from .models import Consultation, Triage, Prescription, PrescriptionItem
from inventory.models import Medicine


class ConsultationSubmitForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['symptoms', 'medical_history', 'severity_description', 'additional_notes']
        widgets = {
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Describe your symptoms in detail...',
            }),
            'medical_history': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Existing conditions, allergies, current medications... (optional)',
            }),
            'severity_description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'e.g. Mild headache since yesterday, moderate fever...',
            }),
            'additional_notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Anything else the clinic should know... (optional)',
            }),
        }
        labels = {
            'symptoms': 'Symptoms *',
            'medical_history': 'Medical History',
            'severity_description': 'Severity Description *',
            'additional_notes': 'Additional Notes',
        }


class QueueAssignForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['status', 'queue_number', 'scheduled_at']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'queue_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'scheduled_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            ('', '— Choose action —'),
            (Consultation.Status.QUEUED, 'Queued — assign queue number'),
            (Consultation.Status.SCHEDULED, 'Scheduled — set appointment time'),
            (Consultation.Status.CANCELLED, 'Cancelled'),
        ]
        self.fields['queue_number'].required = False
        self.fields['scheduled_at'].required = False

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get('status')
        if status == Consultation.Status.QUEUED and not cleaned.get('queue_number'):
            self.add_error('queue_number', 'Queue number is required when status is Queued.')
        if status == Consultation.Status.SCHEDULED and not cleaned.get('scheduled_at'):
            self.add_error('scheduled_at', 'Appointment time is required when status is Scheduled.')
        return cleaned


class TriageForm(forms.ModelForm):
    class Meta:
        model = Triage
        fields = ['blood_pressure', 'temperature', 'pulse_rate', 'urgency', 'notes']
        widgets = {
            'blood_pressure': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '120/80',
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1',
                'placeholder': '36.5', 'min': '30', 'max': '45',
            }),
            'pulse_rate': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '72', 'min': '20', 'max': '300',
            }),
            'urgency': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Additional clinical observations...',
            }),
        }
        labels = {
            'blood_pressure': 'Blood Pressure (mmHg)',
            'temperature': 'Temperature (°C)',
            'pulse_rate': 'Pulse Rate (bpm)',
        }


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['diagnosis', 'treatment_plan']
        widgets = {
            'diagnosis': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Clinical diagnosis...',
            }),
            'treatment_plan': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Treatment plan and recommendations... (optional)',
            }),
        }


class PrescriptionItemForm(forms.Form):
    """Single medicine row in the prescription formset."""
    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.all().order_by('name'),
        required=False,
        empty_label='— Select medicine —',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    quantity = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'min': 1, 'placeholder': 'Qty',
        }),
    )
    instructions = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Take 1 tablet 3x a day after meals',
        }),
    )

    def has_data(self):
        """True if this form row carries meaningful input."""
        cd = getattr(self, 'cleaned_data', {})
        return bool(cd.get('medicine') and cd.get('quantity'))

    def clean(self):
        cleaned = super().clean()
        medicine = cleaned.get('medicine')
        quantity = cleaned.get('quantity')
        instructions = cleaned.get('instructions', '').strip()
        # Partial fill → validation error
        if any([medicine, quantity, instructions]):
            if not medicine:
                self.add_error('medicine', 'Select a medicine.')
            if not quantity:
                self.add_error('quantity', 'Enter a quantity.')
            if not instructions:
                self.add_error('instructions', 'Enter dosage instructions.')
        return cleaned


PrescriptionItemFormSet = formset_factory(PrescriptionItemForm, extra=3)