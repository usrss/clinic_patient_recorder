from django import forms


class AuditLogFilterForm(forms.Form):
    """Form for filtering audit log entries."""

    # Hardcoded role choices matching the User model's Role enum.
    # We avoid referencing the model dynamically here because
    # user_role is a free-text CharField on AuditLog (no choices set).
    _ROLE_CHOICES = [
        ('', 'All Roles'),
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('frontdesk', 'Front Desk'),
        ('patient', 'Patient'),
    ]

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
        choices=_ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    action = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    module = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search descriptions, IDs, names...',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import AuditLog

        # Populate choices dynamically at init time to avoid import-time model issues
        self.fields['action'].choices = [('', 'All Actions')] + list(AuditLog.Action.choices)
        self.fields['module'].choices = [('', 'All Modules')] + list(AuditLog.Module.choices)
        self.fields['status'].choices = [('', 'All Statuses')] + list(AuditLog.Status.choices)
