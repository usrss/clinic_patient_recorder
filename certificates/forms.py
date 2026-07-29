from django import forms
from .models import MedicalCertificate


class CertificateTypeForm(forms.Form):
    """Step 1: Select certificate type."""
    certificate_type = forms.ChoiceField(
        choices=MedicalCertificate.CertificateType.choices,
        widget=forms.RadioSelect(attrs={'class': 'cert-type-radio'}),
        initial=MedicalCertificate.CertificateType.ABSENCES,
    )


class CertificateDetailsForm(forms.ModelForm):
    """Step 2: Certificate details — adapts per type."""

    class Meta:
        model = MedicalCertificate
        fields = [
            'diagnosis',
            'rest_from', 'rest_to',
            'work_assessment', 'return_date', 'restrictions',
            'activity_name', 'fitness_status',
            'remarks',
            'place',
        ]
        widgets = {
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g. Upper respiratory tract infection'}),
            'rest_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'rest_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional notes or restrictions...'}),
            'work_assessment': forms.Select(attrs={'class': 'form-control'}),
            'return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'restrictions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Work restrictions...'}),
            'activity_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Basketball tournament'}),
            'fitness_status': forms.Select(attrs={'class': 'form-control'}),
            'place': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. NORSU Clinic, Bayawan City'}),
        }
        labels = {
            'diagnosis': 'Diagnosis / Findings',
            'rest_from': 'Rest From',
            'rest_to': 'Rest To',
            'remarks': 'Remarks',
            'work_assessment': 'Assessment',
            'return_date': 'Recommended Return Date',
            'restrictions': 'Restrictions / Limitations',
            'activity_name': 'Activity / Event Name',
            'fitness_status': 'Fitness Status',
            'place': 'Place of Issuance',
        }

    def __init__(self, *args, **kwargs):
        self.cert_type = kwargs.pop('cert_type', MedicalCertificate.CertificateType.ABSENCES)
        self.needs_rest_period = kwargs.pop('needs_rest_period', True)
        self.needs_ojt = kwargs.pop('needs_ojt', False)
        self.needs_activities = kwargs.pop('needs_activities', False)
        self.needs_place = kwargs.pop('needs_place', True)
        self.needs_remarks = kwargs.pop('needs_remarks', True)
        self.needs_diagnosis = kwargs.pop('needs_diagnosis', True)
        super().__init__(*args, **kwargs)
        for f in ['rest_from', 'rest_to', 'work_assessment', 'return_date', 'restrictions', 'activity_name', 'fitness_status', 'place']:
            self.fields[f].required = False

    def clean(self):
        cleaned = super().clean()
        rf = cleaned.get('rest_from')
        rt = cleaned.get('rest_to')

        if self.needs_rest_period:
            if not rf:
                self.add_error('rest_from', 'Rest start date is required.')
            if not rt:
                self.add_error('rest_to', 'Rest end date is required.')

        if self.needs_ojt:
            if not cleaned.get('work_assessment'):
                self.add_error('work_assessment', 'Assessment is required.')
            if not cleaned.get('return_date'):
                self.add_error('return_date', 'Return date is required.')

        if self.needs_activities:
            if not cleaned.get('activity_name', '').strip():
                self.add_error('activity_name', 'Activity name is required.')
            if not cleaned.get('fitness_status'):
                self.add_error('fitness_status', 'Fitness status is required.')

        if rf and rt and rt < rf:
            self.add_error('rest_to', 'End date must be after start date.')

        if self.needs_diagnosis and not cleaned.get('diagnosis', '').strip():
            self.add_error('diagnosis', 'Diagnosis is required.')

        return cleaned


class CertificateVoidForm(forms.Form):
    """Form to void an issued certificate."""
    reason = forms.CharField(
        required=True, max_length=500, label='Reason for voiding',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Explain why...'}),
    )

class CertificateTemplateTextForm(forms.Form):
    """Form to edit a single template text slot.

    Sanitization is handled at the model level in CertificateTemplateText.clean().
    """
    text = forms.CharField(
        label='Text',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'style': 'font-family:monospace;font-size:13px;',
            'placeholder': 'Enter prose text with {placeholder} tokens...',
        }),
        help_text='Use {placeholder} tokens for dynamic values.',
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['text'].initial = self.instance.text