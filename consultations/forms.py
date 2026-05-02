from django import forms
from django.forms import formset_factory

from .models import Consultation, Triage, Prescription, PrescriptionItem, CommonDiagnosis
from inventory.models import Medicine
import re


class PatientConsultationForm(forms.ModelForm):
    """Used by a logged-in patient to submit their own consultation request."""
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
                'placeholder': 'Existing conditions, allergies, medications... (optional)',
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


class ConsultationSubmitForm(forms.ModelForm):
    """Used by front desk staff to create a consultation on behalf of a patient."""
    class Meta:
        model = Consultation
        fields = ['patient', 'symptoms', 'medical_history',
                  'severity_description', 'additional_notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Describe symptoms in detail...',
            }),
            'medical_history': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Existing conditions, allergies, medications... (optional)',
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
            'patient': 'Patient *',
            'symptoms': 'Symptoms *',
            'medical_history': 'Medical History',
            'severity_description': 'Severity Description *',
            'additional_notes': 'Additional Notes',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from patients.models import Patient
        self.fields['patient'].queryset = Patient.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')


class QueueAssignForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['status', 'scheduled_at']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            ('', '— Choose action —'),
            (Consultation.Status.QUEUED, 'Queued — assign next queue number automatically'),
            (Consultation.Status.SCHEDULED, 'Scheduled — set appointment time'),
        ]
        self.fields['scheduled_at'].required = False

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get('status')
        if status == Consultation.Status.SCHEDULED and not cleaned.get('scheduled_at'):
            self.add_error('scheduled_at', 'Appointment time is required when status is Scheduled.')
        if status == Consultation.Status.QUEUED:
            cleaned['scheduled_at'] = None
        return cleaned


class TriageForm(forms.ModelForm):

    hypertension = forms.BooleanField(required=False, label='Hypertension')
    diabetes = forms.BooleanField(required=False, label='Diabetes')
    asthma = forms.BooleanField(required=False, label='Asthma')
    cardiac_problems = forms.BooleanField(required=False, label='Cardiac Problems')
    arthritis = forms.BooleanField(required=False, label='Arthritis')
    other_conditions = forms.CharField(required=False, max_length=300, label='Other Conditions',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Other conditions...'}))

    bcg = forms.BooleanField(required=False, label='BCG')
    dpt = forms.BooleanField(required=False, label='DPT')
    opv = forms.BooleanField(required=False, label='OPV')
    hepatitis_b = forms.BooleanField(required=False, label='Hepatitis B')
    measles = forms.BooleanField(required=False, label='Measles')
    tt = forms.BooleanField(required=False, label='TT')

    class Meta:
        model = Triage
        fields = [
            'blood_pressure', 'temperature', 'pulse_rate',
            'respiratory_rate', 'oxygen_saturation', 'weight',
            'urgency', 'notes',
        ]
        widgets = {
            'blood_pressure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '120/80',
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': '36.5',
                'min': '30',
                'max': '45',
            }),
            'pulse_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '72',
                'min': '20',
                'max': '300',
            }),
            'respiratory_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '16',
                'min': '0',
                'max': '100',
            }),
            'oxygen_saturation': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '98.00',
                'min': '0',
                'max': '100',
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '65.00',
                'min': '0',
                'max': '500',
            }),
            'urgency': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional clinical observations...',
            }),
        }
        labels = {
            'blood_pressure': 'Blood Pressure (mmHg)',
            'temperature': 'Temperature (°C)',
            'pulse_rate': 'Pulse Rate (bpm)',
            'respiratory_rate': 'Respiratory Rate (breaths/min)',
            'oxygen_saturation': 'Oxygen Saturation — SpO₂ (%)',
            'weight': 'Weight (kg)',
        }
        help_texts = {
            'respiratory_rate': 'Normal adult rate: 12–20 breaths per minute.',
            'oxygen_saturation': 'Normal range: 95–100%.',
            'weight': 'In kilograms (e.g. 65.00).',
        }

    def clean_blood_pressure(self):
        bp = self.cleaned_data.get('blood_pressure', '').strip()
        if bp and not re.match(r'^\d{2,3}/\d{2,3}$', bp):
            raise forms.ValidationError('Enter blood pressure as systolic/diastolic (e.g. 120/80).')
        return bp

    def clean_temperature(self):
        temp = self.cleaned_data.get('temperature')
        if temp is not None:
            if temp < 30 or temp > 45:
                raise forms.ValidationError('Temperature must be between 30°C and 45°C.')
        return temp

    def clean_pulse_rate(self):
        pulse = self.cleaned_data.get('pulse_rate')
        if pulse is not None:
            if pulse < 20 or pulse > 300:
                raise forms.ValidationError('Pulse rate must be between 20 and 300 bpm.')
        return pulse

    def clean_respiratory_rate(self):
        rate = self.cleaned_data.get('respiratory_rate')
        if rate is not None:
            if rate < 0 or rate > 100:
                raise forms.ValidationError('Respiratory rate must be between 0 and 100 breaths/min.')
        return rate

    def clean_oxygen_saturation(self):
        spo2 = self.cleaned_data.get('oxygen_saturation')
        if spo2 is not None:
            if spo2 < 0 or spo2 > 100:
                raise forms.ValidationError('Oxygen saturation must be between 0 and 100%.')
        return spo2

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None:
            if weight < 0 or weight > 500:
                raise forms.ValidationError('Weight must be between 0 and 500 kg.')
        return weight


class TriageEditForm(forms.ModelForm):
    amendment_reason = forms.CharField(
        required=True, max_length=200,
        label='Reason for amendment *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Blood pressure re-measured, entered wrong value',
        })
    )

    class Meta:
        model = Triage
        fields = [
            'blood_pressure', 'temperature', 'pulse_rate',
            'respiratory_rate', 'oxygen_saturation', 'weight',
            'urgency', 'notes',
        ]
        widgets = {
            'blood_pressure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '120/80',
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '30',
                'max': '45',
            }),
            'pulse_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '20',
                'max': '300',
            }),
            'respiratory_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
            }),
            'oxygen_saturation': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '500',
            }),
            'urgency': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'blood_pressure': 'Blood Pressure (mmHg)',
            'temperature': 'Temperature (°C)',
            'pulse_rate': 'Pulse Rate (bpm)',
            'respiratory_rate': 'Respiratory Rate (breaths/min)',
            'oxygen_saturation': 'Oxygen Saturation — SpO₂ (%)',
            'weight': 'Weight (kg)',
        }

    def clean_blood_pressure(self):
        bp = self.cleaned_data.get('blood_pressure', '').strip()
        if bp and not re.match(r'^\d{2,3}/\d{2,3}$', bp):
            raise forms.ValidationError('Enter blood pressure as systolic/diastolic (e.g. 120/80).')
        return bp

    def clean_temperature(self):
        temp = self.cleaned_data.get('temperature')
        if temp is not None:
            if temp < 30 or temp > 45:
                raise forms.ValidationError('Temperature must be between 30°C and 45°C.')
        return temp

    def clean_pulse_rate(self):
        pulse = self.cleaned_data.get('pulse_rate')
        if pulse is not None:
            if pulse < 20 or pulse > 300:
                raise forms.ValidationError('Pulse rate must be between 20 and 300 bpm.')
        return pulse

    def clean_respiratory_rate(self):
        rate = self.cleaned_data.get('respiratory_rate')
        if rate is not None:
            if rate < 0 or rate > 100:
                raise forms.ValidationError('Respiratory rate must be between 0 and 100 breaths/min.')
        return rate

    def clean_oxygen_saturation(self):
        spo2 = self.cleaned_data.get('oxygen_saturation')
        if spo2 is not None:
            if spo2 < 0 or spo2 > 100:
                raise forms.ValidationError('Oxygen saturation must be between 0 and 100%.')
        return spo2

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None:
            if weight < 0 or weight > 500:
                raise forms.ValidationError('Weight must be between 0 and 500 kg.')
        return weight


class PrescriptionForm(forms.ModelForm):
    diagnosis_select = forms.ModelChoiceField(
        queryset=CommonDiagnosis.objects.all().order_by('name'),
        required=False,
        label='Common Diagnosis',
        widget=forms.Select(attrs={'class': 'reg-input'}),
    )

    class Meta:
        model = Prescription
        fields = ['diagnosis', 'treatment_plan']
        widgets = {
            'diagnosis': forms.Textarea(attrs={
                'class': 'reg-input',
                'rows': 3,
                'placeholder': 'Or type a custom diagnosis...',
            }),
            'treatment_plan': forms.Textarea(attrs={
                'class': 'reg-input',
                'rows': 3,
                'placeholder': 'Treatment plan and recommendations...',
            }),
        }


class PrescriptionItemForm(forms.Form):
    """
    Combined medicine row: inventory dropdown + free-text dosing fields.
    Doctor can select from inventory OR type a custom medicine name.
    Auto-deducts stock when inventory medicine is selected.
    """
    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.filter(quantity__gt=0).order_by('name'),
        required=False,
        label='Medicine',
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
    )
    medicine_name = forms.CharField(
        required=False,
        max_length=200,
        label='Or custom medicine name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type if not in inventory',
            'autocomplete': 'off',
        }),
    )
    dosage = forms.CharField(
        required=False,
        max_length=100,
        label='Dosage',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 500mg',
        }),
    )
    frequency = forms.CharField(
        required=False,
        max_length=100,
        label='Frequency',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 3x a day',
        }),
    )
    duration = forms.CharField(
        required=False,
        max_length=100,
        label='Duration',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 7 days',
        }),
    )
    quantity = forms.IntegerField(
        required=False,
        min_value=1,
        label='Quantity to dispense',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'placeholder': 'Number of units',
        }),
    )
    instructions = forms.CharField(
        required=False,
        max_length=200,
        label='Instructions (optional)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Take after meals',
        }),
    )

    def has_data(self):
        """Return True if this row has any meaningful input."""
        cd = getattr(self, 'cleaned_data', {})
        return bool(
            cd.get('medicine') or
            cd.get('medicine_name') or
            cd.get('dosage')
        )

    def clean(self):
        cleaned = super().clean()
        medicine = cleaned.get('medicine')
        medicine_name = cleaned.get('medicine_name', '').strip()
        dosage = cleaned.get('dosage', '').strip()
        frequency = cleaned.get('frequency', '').strip()
        duration = cleaned.get('duration', '').strip()
        quantity = cleaned.get('quantity')
        instructions = cleaned.get('instructions', '').strip()

        # If any field has data, validate the row
        any_filled = any([medicine, medicine_name, dosage, frequency, duration, quantity, instructions])
        if any_filled:
            # Either inventory medicine OR custom name required
            if not medicine and not medicine_name:
                self.add_error('medicine', 'Select a medicine from inventory or type a custom name.')
                self.add_error('medicine_name', 'Select a medicine from inventory or type a custom name.')
            if not dosage:
                self.add_error('dosage', 'Dosage is required.')
            if not frequency:
                self.add_error('frequency', 'Frequency is required.')
            if not duration:
                self.add_error('duration', 'Duration is required.')

            # If inventory medicine selected, quantity is required and must not exceed stock
            if medicine:
                if not quantity:
                    self.add_error('quantity', 'Quantity is required when dispensing from inventory.')
                elif quantity > medicine.quantity:
                    self.add_error(
                        'quantity',
                        f'Insufficient stock — only {medicine.quantity} {medicine.get_unit_display()}(s) available.'
                    )
        return cleaned


# Replace the formset
PrescriptionMedicineFormSet = formset_factory(PrescriptionItemForm, extra=1)


# Used by the existing inventory-linked prescribe view (kept for backward compat)
class PrescriptionItemInventoryForm(forms.Form):
    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.all().order_by('name'),
        required=False,
        empty_label='— Select medicine —',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    quantity = forms.IntegerField(
        required=False, min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'min': 1, 'placeholder': 'Qty',
        }),
    )
    instructions = forms.CharField(
        required=False, max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Take 1 tablet 3x a day after meals',
        }),
    )

    def has_data(self):
        cd = getattr(self, 'cleaned_data', {})
        return bool(cd.get('medicine') and cd.get('quantity'))

    def clean(self):
        cleaned = super().clean()
        medicine     = cleaned.get('medicine')
        quantity     = cleaned.get('quantity')
        instructions = cleaned.get('instructions', '').strip()
        if any([medicine, quantity, instructions]):
            if not medicine:
                self.add_error('medicine', 'Select a medicine.')
            if not quantity:
                self.add_error('quantity', 'Enter a quantity.')
            if medicine and quantity and quantity > medicine.quantity:
                self.add_error(
                    'quantity',
                    f'Insufficient stock — only {medicine.quantity} '
                    f'{medicine.get_unit_display()}(s) available.'
                )
        return cleaned


# The formset used in the existing inventory-based prescribe view
PrescriptionItemFormSet = formset_factory(PrescriptionItemInventoryForm, extra=3)

# The new free-text medicine formset for the doctor prescription form
PrescriptionMedicineFormSet = formset_factory(PrescriptionItemForm, extra=1)