"""
Migration: Convert existing 'dental' certificate_type records to 'standard'.

The DENTAL certificate type has been removed from the model since it shared
the same .docx template as STANDARD and had no dedicated template file.
Existing dental records are converted to standard so they continue to work.
"""
from django.db import migrations


def convert_dental_to_standard(apps, schema_editor):
    MedicalCertificate = apps.get_model('certificates', 'MedicalCertificate')
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')

    updated_certs = MedicalCertificate.objects.filter(
        certificate_type='dental'
    ).update(certificate_type='standard')
    print(f"  Converted {updated_certs} MedicalCertificate records from 'dental' to 'standard'")

    updated_templates = CertificateTemplateText.objects.filter(
        certificate_type='dental'
    ).update(certificate_type='standard')
    print(f"  Converted {updated_templates} CertificateTemplateText records from 'dental' to 'standard'")


def reverse_convert(apps, schema_editor):
    """No-op — we cannot know which records were originally dental."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('certificates', '0011_alter_certificatetemplatetext_certificate_type_and_more'),
    ]

    operations = [
        migrations.RunPython(convert_dental_to_standard, reverse_convert),
    ]
