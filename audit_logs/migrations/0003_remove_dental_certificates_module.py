"""
Migration: Convert existing 'Dental Certificates' module entries to 'Medical Certificates'.

The DENTAL_CERTIFICATES module choice has been removed from the AuditLog model
since the DENTAL certificate type was removed from the certificates app.
Existing audit log entries with module='Dental Certificates' are converted
to 'Medical Certificates' so they continue to display correctly.
"""
from django.db import migrations


def convert_dental_to_medical(apps, schema_editor):
    AuditLog = apps.get_model('audit_logs', 'AuditLog')

    updated = AuditLog.objects.filter(
        module='Dental Certificates'
    ).update(module='Medical Certificates')
    print(f"  Converted {updated} audit log entries from 'Dental Certificates' to 'Medical Certificates'")


def reverse_convert(apps, schema_editor):
    """No-op — we cannot know which records were originally Dental Certificates."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('audit_logs', '0002_rename_audit_log_timestamp_idx_audit_logs__timesta_63825c_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(convert_dental_to_medical, reverse_convert),
    ]
