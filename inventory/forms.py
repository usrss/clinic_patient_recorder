from django import forms
from .models import Medicine, StockMovement


class MedicineForm(forms.ModelForm):
    """Form for creating/editing medicines."""

    class Meta:
        model = Medicine
        fields = [
            'name', 'generic_name', 'description',
            'quantity', 'unit', 'low_stock_threshold',
            'batch_number', 'expiry_date', 'supplier',
            'cost_per_unit'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Paracetamol 500mg'
            }),
            'generic_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Acetaminophen'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Uses, side effects, contraindications...'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_per_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }


class MedicineRestockForm(forms.Form):
    """Form for adding stock to a medicine."""

    quantity = forms.IntegerField(
        min_value=1,
        label='Quantity to Add',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter quantity'
        })
    )
    reason = forms.CharField(
        required=False,
        max_length=200,
        label='Reason (optional)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., New purchase, replacement'
        })
    )
    batch_number = forms.CharField(
        required=False,
        max_length=100,
        label='Batch Number (optional)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Batch/lot number'
        })
    )
    expiry_date = forms.DateField(
        required=False,
        label='Expiry Date (optional)',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class MedicineDeductForm(forms.Form):
    """Form for dispensing/deducting medicine (used by prescriptions)."""

    quantity = forms.IntegerField(
        min_value=1,
        label='Quantity',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quantity to dispense'
        })
    )
    reason = forms.CharField(
        max_length=200,
        label='Reason',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Consultation ID: 12345'
        })
    )


class MedicineSearchForm(forms.Form):
    """Form for searching medicines."""

    query = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, generic name...',
            'autofocus': True
        })
    )
    low_stock_only = forms.BooleanField(
        required=False,
        label='Show low stock items only',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )