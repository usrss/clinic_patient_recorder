from django.db import migrations, models


TYPE_MAP = {
    'standard': 'absences',
    'fit_to_work': 'ojt',
    'fit_to_play': 'activities',
}
REVERSE_MAP = {v: k for k, v in TYPE_MAP.items()}


def update_certificate_types(apps, schema_editor):
    MedicalCertificate = apps.get_model('certificates', 'MedicalCertificate')
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')

    for old, new in TYPE_MAP.items():
        MedicalCertificate.objects.filter(certificate_type=old).update(certificate_type=new)
        CertificateTemplateText.objects.filter(certificate_type=old).update(certificate_type=new)


def reverse_certificate_types(apps, schema_editor):
    MedicalCertificate = apps.get_model('certificates', 'MedicalCertificate')
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')

    for new, old in REVERSE_MAP.items():
        MedicalCertificate.objects.filter(certificate_type=new).update(certificate_type=old)
        CertificateTemplateText.objects.filter(certificate_type=new).update(certificate_type=old)


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0014_update_template_text_body'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certificatetemplatetext',
            name='certificate_type',
            field=models.CharField(choices=[('absences', 'Medical Certificate — Absences (Classes/Work)'), ('ojt', 'Medical Certificate — OJT'), ('activities', 'Medical Certificate — Activities/Training/Seminars')], max_length=20),
        ),
        migrations.AlterField(
            model_name='medicalcertificate',
            name='certificate_type',
            field=models.CharField(choices=[('absences', 'Medical Certificate — Absences (Classes/Work)'), ('ojt', 'Medical Certificate — OJT'), ('activities', 'Medical Certificate — Activities/Training/Seminars')], default='absences', max_length=20),
        ),
        migrations.RunPython(
            update_certificate_types,
            reverse_certificate_types,
        ),
    ]
