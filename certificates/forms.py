from django import forms
from .models import MedicalCertificate


class MedicalCertificateForm(forms.ModelForm):
    class Meta:
        model = MedicalCertificate
        fields = ['certificate_type', 'diagnosis', 'rest_from', 'rest_to', 'remarks']
        widgets = {
            'certificate_type': forms.Select(attrs={'class': 'form-control'}),
            'diagnosis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'e.g. Upper respiratory tract infection',
            }),
            'rest_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'rest_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'e.g. Fit to return to school after rest period',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rest_from'].required = False
        self.fields['rest_to'].required = False

    def clean(self):
        cleaned = super().clean()
        cert_type = cleaned.get('certificate_type')
        rest_from = cleaned.get('rest_from')
        rest_to = cleaned.get('rest_to')

        # Rest dates required for standard certificates
        if cert_type == MedicalCertificate.CertificateType.STANDARD:
            if not rest_from:
                self.add_error('rest_from', 'Rest from date is required for standard certificates.')
            if not rest_to:
                self.add_error('rest_to', 'Rest to date is required for standard certificates.')

        if rest_from and rest_to and rest_to < rest_from:
            self.add_error('rest_to', 'End date must be after start date.')

        return cleaned