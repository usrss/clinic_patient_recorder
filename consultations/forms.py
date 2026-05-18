from django import forms
from django.forms import formset_factory

from .models import Consultation, Triage, Prescription, PrescriptionItem, CommonDiagnosis, FollowUpProgress
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


class ConsultationSubmitForm(forms.Form):
    """
    Used by front desk staff to create a consultation on behalf of a patient.
    Supports walk-in patients who are not yet registered.
    """

    # ── Patient lookup fields (always visible) ──────────────────────────────
    patient_id = forms.CharField(
        max_length=30,
        label='Patient ID Number *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 2023-01234',
            'autocomplete': 'off',
        }),
    )
    first_name = forms.CharField(
        max_length=150,
        label='First Name *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name',
        }),
    )
    last_name = forms.CharField(
        max_length=150,
        label='Last Name *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name',
        }),
    )
    birthdate = forms.DateField(
        label='Birthdate *',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
    )

    # ── New patient fields (shown only when patient NOT found) ──────────────
    sex = forms.ChoiceField(
        choices=[('', '— Select —'), ('M', 'Male'), ('F', 'Female')],
        required=False,
        label='Sex *',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    contact_number = forms.CharField(
        max_length=30,
        required=False,
        label='Contact Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 09171234567',
        }),
    )

    # ── Consultation fields ─────────────────────────────────────────────────
    symptoms = forms.CharField(
        label='Symptoms *',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 4,
            'placeholder': 'Describe symptoms in detail...',
        }),
    )
    severity_description = forms.CharField(
        label='Severity Description *',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2,
            'placeholder': 'e.g. Mild headache since yesterday, moderate fever...',
        }),
    )
    medical_history = forms.CharField(
        required=False,
        label='Medical History',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'Existing conditions, allergies, medications... (optional)',
        }),
    )
    additional_notes = forms.CharField(
        required=False,
        label='Additional Notes',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2,
            'placeholder': 'Anything else the clinic should know... (optional)',
        }),
    )

    def clean_patient_id(self):
        pid = self.cleaned_data['patient_id'].strip()
        if not pid:
            raise forms.ValidationError('Patient ID is required.')
        return pid

    def clean(self):
        cleaned = super().clean()
        patient_id = cleaned.get('patient_id', '').strip()

        from patients.models import Patient
        from accounts.models import User

        existing_patient = Patient.objects.filter(patient_id=patient_id).first()

        if existing_patient:
            # Patient found — new patient fields not required
            cleaned['_patient'] = existing_patient
            return cleaned

        # Patient NOT found — validate new patient fields
        sex = cleaned.get('sex', '')
        if not sex:
            self.add_error('sex', 'Sex is required for new patients.')

        # Check that a User with this patient_id doesn't already exist
        if User.objects.filter(username=patient_id).exists():
            self.add_error(
                'patient_id',
                'This ID is already linked to a user account but no patient record was found. '
                'Please contact an administrator.'
            )

        cleaned['_patient'] = None
        return cleaned


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


# ── Choice constants shared between PrescriptionItemForm and the template ──────

DOSAGE_CHOICES = [
    ('', '— Select —'),
    ('500mg', '500mg'), ('250mg', '250mg'), ('200mg', '200mg'),
    ('100mg', '100mg'), ('50mg', '50mg'), ('25mg', '25mg'),
    ('10mg', '10mg'), ('5mg', '5mg'),
    ('10ml', '10ml'), ('5ml', '5ml'), ('2.5ml', '2.5ml'),
    ('other', 'Other (type below)…'),
]

FREQUENCY_CHOICES = [
    ('', '— Select —'),
    ('Once daily', 'Once daily'),
    ('2x a day', '2x a day'),
    ('3x a day', '3x a day'),
    ('4x a day', '4x a day'),
    ('Every 4 hours', 'Every 4 hours'),
    ('Every 6 hours', 'Every 6 hours'),
    ('Every 8 hours', 'Every 8 hours'),
    ('As needed', 'As needed'),
    ('other', 'Other (type below)…'),
]

DURATION_CHOICES = [
    ('', '— Select —'),
    ('1 day', '1 day'),
    ('3 days', '3 days'),
    ('5 days', '5 days'),
    ('7 days', '7 days'),
    ('10 days', '10 days'),
    ('14 days', '14 days'),
    ('1 month', '1 month'),
    ('other', 'Other (type below)…'),
]

INSTRUCTIONS_CHOICES = [
    ('', '— Select —'),
    ('Take after meals', 'Take after meals'),
    ('Take before meals', 'Take before meals'),
    ('Take on empty stomach', 'Take on empty stomach'),
    ('Take with food', 'Take with food'),
    ('Apply topically', 'Apply topically'),
    ('As directed', 'As directed'),
    ('other', 'Other (type below)…'),
]

_SELECT_ATTRS = {'class': 'reg-input med-select'}
_TEXT_ATTRS   = {'class': 'reg-input med-other', 'autocomplete': 'off', 'placeholder': 'Specify…'}


class PrescriptionItemForm(forms.Form):
    """
    One medicine row in the prescription formset.

    KEY DESIGN: inventory mode and custom mode use completely separate field names
    (inv_dosage vs cus_dosage, etc.) so there are never two <input name="meds-N-dosage">
    elements in the DOM at the same time — which was the root cause of the original bug.

    clean() reads the active mode from the hidden `source` field, resolves any
    "Other…" free-text overrides, then writes the canonical keys
    (dosage / frequency / duration / instructions) so views.py is unchanged.
    """

    # ── source selector (set by JS when radio changes) ─────────────────────────
    source = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'class': 'med-source-hidden'}),
    )

    # ── inventory mode fields ───────────────────────────────────────────────────
    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.filter(quantity__gt=0).order_by('name'),
        required=False,
        label='Medicine',
        widget=forms.Select(attrs={'class': 'reg-input'}),
    )
    inv_dosage = forms.ChoiceField(
        choices=DOSAGE_CHOICES, required=False, label='Dosage',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    inv_dosage_other = forms.CharField(
        required=False, max_length=100,
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'e.g. 750mg'}),
    )
    inv_frequency = forms.ChoiceField(
        choices=FREQUENCY_CHOICES, required=False, label='Frequency',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    inv_frequency_other = forms.CharField(
        required=False, max_length=100,
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'e.g. Every 12 hours'}),
    )
    inv_duration = forms.ChoiceField(
        choices=DURATION_CHOICES, required=False, label='Duration',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    inv_duration_other = forms.CharField(
        required=False, max_length=100,
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'e.g. 3 weeks'}),
    )
    inv_instructions = forms.ChoiceField(
        choices=INSTRUCTIONS_CHOICES, required=False, label='Instructions',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    inv_instructions_other = forms.CharField(
        required=False, max_length=200,
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'e.g. Dissolve in water'}),
    )
    quantity = forms.IntegerField(
        required=False, min_value=1, label='Qty',
        widget=forms.NumberInput(attrs={'class': 'reg-input', 'min': 1, 'placeholder': 'Units'}),
    )

    # ── custom mode fields ──────────────────────────────────────────────────────
    medicine_name = forms.CharField(
        required=False, max_length=200, label='Medicine Name',
        widget=forms.TextInput(attrs={
            'class': 'reg-input',
            'placeholder': 'e.g. Betadine Gargle',
            'autocomplete': 'off',
        }),
    )
    cus_dosage = forms.ChoiceField(
        choices=DOSAGE_CHOICES, required=False, label='Dosage',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    cus_dosage_other = forms.CharField(
        required=False, max_length=100,
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'e.g. 750mg'}),
    )
    cus_frequency = forms.ChoiceField(
        choices=FREQUENCY_CHOICES, required=False, label='Frequency',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    cus_frequency_other = forms.CharField(
        required=False, max_length=100,
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'e.g. Every 12 hours'}),
    )
    cus_duration = forms.ChoiceField(
        choices=DURATION_CHOICES, required=False, label='Duration',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    cus_duration_other = forms.CharField(
        required=False, max_length=100,
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'e.g. 3 weeks'}),
    )
    cus_instructions = forms.ChoiceField(
        choices=INSTRUCTIONS_CHOICES, required=False, label='Instructions',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    cus_instructions_other = forms.CharField(
        required=False, max_length=200,
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'e.g. Dissolve in water'}),
    )

    # ── helpers ─────────────────────────────────────────────────────────────────

    def _resolve(self, select_val, other_val):
        """Return the free-text value if 'other' was chosen, else the select value."""
        if select_val == 'other':
            return (other_val or '').strip()
        return (select_val or '').strip()

    def has_data(self):
        cd = getattr(self, 'cleaned_data', {})
        return bool(cd.get('medicine') or cd.get('medicine_name', '').strip())

    def clean(self):
        cleaned = super().clean()
        source        = (cleaned.get('source') or 'inventory').strip()
        medicine      = cleaned.get('medicine')
        medicine_name = (cleaned.get('medicine_name') or '').strip()

        # Determine active mode
        if source == 'custom' or (not medicine and medicine_name):
            mode = 'custom'
        else:
            mode = 'inventory'

        # Empty row — nothing to validate
        if mode == 'inventory' and not medicine:
            return cleaned
        if mode == 'custom' and not medicine_name:
            return cleaned

        # Resolve canonical field values from whichever mode is active
        if mode == 'inventory':
            dosage       = self._resolve(cleaned.get('inv_dosage', ''),       cleaned.get('inv_dosage_other', ''))
            frequency    = self._resolve(cleaned.get('inv_frequency', ''),    cleaned.get('inv_frequency_other', ''))
            duration     = self._resolve(cleaned.get('inv_duration', ''),     cleaned.get('inv_duration_other', ''))
            instructions = self._resolve(cleaned.get('inv_instructions', ''), cleaned.get('inv_instructions_other', ''))
            quantity     = cleaned.get('quantity')
        else:
            dosage       = self._resolve(cleaned.get('cus_dosage', ''),       cleaned.get('cus_dosage_other', ''))
            frequency    = self._resolve(cleaned.get('cus_frequency', ''),    cleaned.get('cus_frequency_other', ''))
            duration     = self._resolve(cleaned.get('cus_duration', ''),     cleaned.get('cus_duration_other', ''))
            instructions = self._resolve(cleaned.get('cus_instructions', ''), cleaned.get('cus_instructions_other', ''))
            quantity     = None  # custom medicines never deduct from inventory

        # Write canonical keys so views.py reads them uniformly
        cleaned['dosage']       = dosage
        cleaned['frequency']    = frequency
        cleaned['duration']     = duration
        cleaned['instructions'] = instructions
        cleaned['quantity']     = quantity
        cleaned['_mode']        = mode

        # Validation
        prefix = 'inv' if mode == 'inventory' else 'cus'
        if not dosage:
            self.add_error(f'{prefix}_dosage', 'Dosage is required.')
        if not frequency:
            self.add_error(f'{prefix}_frequency', 'Frequency is required.')
        if not duration:
            self.add_error(f'{prefix}_duration', 'Duration is required.')

        if mode == 'inventory' and medicine:
            if not quantity:
                self.add_error('quantity', 'Quantity is required when dispensing from inventory.')
            elif quantity and quantity > medicine.quantity:
                self.add_error(
                    'quantity',
                    f'Insufficient stock — only {medicine.quantity} '
                    f'{medicine.get_unit_display()}(s) available.',
                )

        return cleaned


# ── Formsets ────────────────────────────────────────────────────────────────────

class PrescriptionItemInventoryForm(forms.Form):
    """Legacy inventory-only form — kept for backward compatibility."""
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
                    f'{medicine.get_unit_display()}(s) available.',
                )
        return cleaned


# The legacy inventory-based formset (kept for backward compat)
PrescriptionItemFormSet = formset_factory(PrescriptionItemInventoryForm, extra=3)

# The active formset used by the prescribe view
PrescriptionMedicineFormSet = formset_factory(PrescriptionItemForm, extra=1)

# ─── FOLLOW-UP / CONSULTATION CONTINUATION FORMS ─────────────────────────────


class FollowUpProgressForm(forms.ModelForm):
    """
    Form for recording each follow-up visit's clinical data.
    Used by doctors/staff when continuing a consultation.
    """
    requires_follow_up = forms.BooleanField(
        required=False,
        label='Patient requires another follow-up visit',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    recommended_follow_up_date = forms.DateField(
        required=False,
        label='Recommended follow-up date',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
    )

    class Meta:
        model = FollowUpProgress
        fields = [
            'symptoms', 'assessment', 'treatment_notes',
            'recommendations', 'notes',
        ]
        widgets = {
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Current symptoms since last visit...',
            }),
            'assessment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Doctor assessment for this follow-up visit...',
            }),
            'treatment_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Treatment administered or adjusted...',
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Recommendations for the patient...',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes...',
            }),
        }
        labels = {
            'symptoms': 'Current Symptoms *',
            'assessment': 'Assessment',
            'treatment_notes': 'Treatment Notes',
            'recommendations': 'Recommendations',
            'notes': 'Additional Notes',
        }

    def clean(self):
        cleaned = super().clean()
        requires_follow_up = cleaned.get('requires_follow_up')
        recommended_date = cleaned.get('recommended_follow_up_date')

        if requires_follow_up and not recommended_date:
            self.add_error(
                'recommended_follow_up_date',
                'Please set a recommended follow-up date when follow-up is required.'
            )
        return cleaned


class CloseConsultationForm(forms.ModelForm):
    """
    Form for closing a consultation case.
    """
    class Meta:
        model = Consultation
        fields = ['closure_notes']
        widgets = {
            'closure_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Reason for closing this case (e.g., Patient recovered, referred to specialist)...',
            }),
        }
        labels = {
            'closure_notes': 'Closure Notes *',
        }


class ConsultationStatusUpdateForm(forms.ModelForm):
    """
    Allow staff to update consultation status manually.
    """
    class Meta:
        model = Consultation
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit status choices based on current state
        self.fields['status'].choices = [
            (Consultation.Status.ACTIVE_FOLLOW_UP, 'Active - Follow-up'),
            (Consultation.Status.CLOSED, 'Closed'),
            (Consultation.Status.COMPLETED, 'Completed'),
        ]