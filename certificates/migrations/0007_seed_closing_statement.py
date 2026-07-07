from django.db import migrations


def seed_closing_statement(apps, schema_editor):
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')
    CertificateTemplateText.objects.update_or_create(
        certificate_type='fit_to_work',
        slot_key='closing_statement',
        defaults={
            'text': 'This certificate is issued upon the request of the patient for whatever '
                    'legal purpose it may serve.',
        },
    )
    CertificateTemplateText.objects.update_or_create(
        certificate_type='fit_to_play',
        slot_key='closing_statement',
        defaults={
            'text': 'This certificate is issued upon the request of the patient for whatever '
                    'legal purpose it may serve.',
        },
    )


def reverse_seed(apps, schema_editor):
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')
    CertificateTemplateText.objects.filter(
        certificate_type__in=('fit_to_work', 'fit_to_play'),
        slot_key='closing_statement',
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0006_seed_certificate_template_text'),
    ]

    operations = [
        migrations.RunPython(seed_closing_statement, reverse_seed),
    ]
