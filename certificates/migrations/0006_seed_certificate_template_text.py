from django.db import migrations


def seed_template_text(apps, schema_editor):
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')
    CertificateTemplateText.objects.bulk_create([
        # ── Standard ─────────────────────────────────────────────────
        CertificateTemplateText(
            certificate_type='standard',
            slot_key='diagnosis_statement',
            text='This is to certify that {patient_name}, {age} years of age, '
                 '{sex}, {college_info}was examined and treated at this clinic on {exam_date}.',
        ),
        CertificateTemplateText(
            certificate_type='standard',
            slot_key='diagnosis_line',
            text='Diagnosis: {diagnosis}',
        ),
        CertificateTemplateText(
            certificate_type='standard',
            slot_key='rest_period_single',
            text='The patient is advised to rest on {rest_date}.',
        ),
        CertificateTemplateText(
            certificate_type='standard',
            slot_key='rest_period_range',
            text='The patient is advised to rest from {rest_from} to {rest_to}.',
        ),
        CertificateTemplateText(
            certificate_type='standard',
            slot_key='closing_statement',
            text='This certificate is issued upon the request of the patient for '
                 'whatever legal purpose it may serve.',
        ),
        # ── Fit-to-Work ──────────────────────────────────────────────
        CertificateTemplateText(
            certificate_type='fit_to_work',
            slot_key='statement',
            text='This is to certify that {patient_name}, {age} years of age, '
                 '{sex}, {position_info}has been examined and found to be PHYSICALLY FIT '
                 'to return to work.',
        ),
        CertificateTemplateText(
            certificate_type='fit_to_work',
            slot_key='findings_line',
            text='Findings: {diagnosis}',
        ),
        # ── Fit-to-Play ──────────────────────────────────────────────
        CertificateTemplateText(
            certificate_type='fit_to_play',
            slot_key='statement',
            text='This is to certify that {patient_name}, {age} years of age, '
                 '{sex}, {college_info}has been examined and found to be PHYSICALLY FIT '
                 'to participate in:',
        ),
        CertificateTemplateText(
            certificate_type='fit_to_play',
            slot_key='findings_line',
            text='Findings: {diagnosis}',
        ),
    ])


def reverse_seed(apps, schema_editor):
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')
    CertificateTemplateText.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0005_certificatetemplatetext_certificatetemplatechangelog_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_template_text, reverse_seed),
    ]
