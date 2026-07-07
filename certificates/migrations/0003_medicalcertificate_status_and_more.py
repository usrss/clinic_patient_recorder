"""Migration: Add new fields to MedicalCertificate + CertificateAuditLog model."""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0006_academicyearsettings_patient_archived_at_and_more'),
        ('certificates', '0002_medicalcertificate_certificate_type_and_more'),
    ]

    operations = [
        # ── Add new fields to MedicalCertificate ─────────────────────────
        migrations.AddField(
            model_name='medicalcertificate',
            name='activity_name',
            field=models.CharField(blank=True, help_text='Fit-to-Play: name of the sports/activity', max_length=200),
        ),
        migrations.AddField(
            model_name='medicalcertificate',
            name='certificate_number',
            field=models.CharField(blank=True, help_text='Format: MC-YYYY-XXXXXX (assigned on issue)', max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='medicalcertificate',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default='2026-01-01'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='medicalcertificate',
            name='diagnosis_snapshot',
            field=models.TextField(blank=True, help_text='Frozen diagnosis at time of issuance (historical accuracy)'),
        ),
        migrations.AddField(
            model_name='medicalcertificate',
            name='fitness_status',
            field=models.CharField(blank=True, choices=[('cleared', 'Cleared'), ('not_cleared', 'Not Cleared')], help_text='Fit-to-Play: clearance result', max_length=20),
        ),
        migrations.AddField(
            model_name='medicalcertificate',
            name='patient',
            field=models.ForeignKey(blank=True, help_text='Direct patient reference (denormalized for history)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='certificates', to='patients.patient'),
        ),
        migrations.AddField(
            model_name='medicalcertificate',
            name='restrictions',
            field=models.TextField(blank=True, help_text='Work restrictions if applicable'),
        ),
        migrations.AddField(
            model_name='medicalcertificate',
            name='return_date',
            field=models.DateField(blank=True, help_text='Fit-to-Work: recommended return date', null=True),
        ),
        migrations.AddField(
            model_name='medicalcertificate',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('issued', 'Issued'), ('voided', 'Voided')], db_index=True, default='draft', max_length=10),
        ),
        migrations.AddField(
            model_name='medicalcertificate',
            name='template_version',
            field=models.CharField(default='2.0', help_text='Print template version used', max_length=10),
        ),
        migrations.AddField(
            model_name='medicalcertificate',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='medicalcertificate',
            name='work_assessment',
            field=models.CharField(blank=True, choices=[('fit_to_return', 'Physically fit to return to work'), ('fit_with_restrictions', 'Fit with restrictions')], help_text='Fit-to-Work assessment result', max_length=50),
        ),

        # ── Change OneToOneField to ForeignKey ──────────────────────────
        migrations.AlterField(
            model_name='medicalcertificate',
            name='consultation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certificates', to='consultations.consultation', help_text='The consultation this certificate belongs to'),
        ),

        # ── Change doctor nullability ───────────────────────────────────
        migrations.AlterField(
            model_name='medicalcertificate',
            name='doctor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='certificates_issued', to=settings.AUTH_USER_MODEL),
        ),

        # ── Update issued_at to be nullable (set at issue time) ─────────
        migrations.AlterField(
            model_name='medicalcertificate',
            name='issued_at',
            field=models.DateTimeField(blank=True, help_text='When the certificate was issued', null=True),
        ),

        # ── Update ordering ─────────────────────────────────────────────
        migrations.AlterModelOptions(
            name='medicalcertificate',
            options={'ordering': ['-created_at'], 'verbose_name': 'Medical Certificate', 'verbose_name_plural': 'Medical Certificates'},
        ),

        # ── Add indexes ─────────────────────────────────────────────────
        migrations.AddIndex(
            model_name='medicalcertificate',
            index=models.Index(fields=['status', '-created_at'], name='certificate_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='medicalcertificate',
            index=models.Index(fields=['certificate_number'], name='certificate_number_idx'),
        ),

        # ── Create CertificateAuditLog ──────────────────────────────────
        migrations.CreateModel(
            name='CertificateAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(db_index=True, help_text='e.g. created, issued, printed, viewed, voided', max_length=20)),
                ('details', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('certificate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='certificates.medicalcertificate')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Certificate Audit Log',
                'verbose_name_plural': 'Certificate Audit Logs',
                'ordering': ['-timestamp'],
            },
        ),
    ]
