from django import forms
from .models import AuditLog


class AuditLogFilterForm(forms.Form):
    """Form for filtering audit log entries."""

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    user = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name...',
        }),
    )
    role = forms.ChoiceField(
        required=False,
        choices=[('', 'All Roles')] + list(AuditLog._meta.get_field('user_role').choices or []),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    action = forms.ChoiceField(
        required=False,
        choices=[('', 'All Actions')] + list(AuditLog.Action.choices),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    module = forms.ChoiceField(
        required=False,
        choices=[('', 'All Modules')] + list(AuditLog.Module.choices),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + list(AuditLog.Status.choices),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search descriptions, IDs, names...',
        }),
    )
