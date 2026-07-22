from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0012_remove_dental_certificate_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicalcertificate',
            name='place',
            field=models.CharField(
                blank=True,
                default='Negros Oriental State University, Bayawan-Sta. Catalina Campus, Bayawan City, Philippines',
                help_text='Clinic location / place of issuance',
                max_length=255,
            ),
        ),
    ]
