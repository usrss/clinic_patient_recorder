from django.db import migrations


# ── New body text for each certificate type ───────────────────────────────

BODY_TEXTS = {
    'standard': (
        'This is to certify that {patient_name}, {age} years old and a '
        '{course} student in this campus, has been consulted '
        'in the clinic, due to the following complaints and assessments.\n\n'
        'Complaint/s:\n• {diagnosis}\n\n'
        'Assessment/s:\n• {diagnosis}\n\n'
        'Remark/s:\n• {remarks}\n\n'
        'Given this {day} day of {month}, {year} at {place}, '
        'for whatever legal purpose this may serve.'
    ),
    'fit_to_work': (
        'This is to certify that {patient_name}, {age} years old, a '
        '{course} student in this campus, was seen and examined through '
        'Medical/Physical Examination by the undersigned and is Physically '
        'Fit to undergo {activity_name} on {exam_date} at {place}.\n\n'
        'Vital Signs:\n'
        'Temp.: {temperature}   BP: {blood_pressure}   '
        'PR: {pulse_rate}   RR: {respiratory_rate}\n\n'
        'Issued this {day} day of {month}, {year} at {place}.\n\n'
        'Remarks:\n{remarks}'
    ),
    'fit_to_play': (
        'This is to certify that {patient_name}, {age} years old, a '
        '{course} student in this campus, has seen and examined through '
        'medical/Physical Examination by the undersigned and is Physically '
        'Fit to participate the {activity_name} on {exam_date} at {place}.\n\n'
        'Issued this {day} day of {month}, {year} at {place}.\n\n'
        'Vital Signs:\n'
        'Temp.: {temperature}   BP: {blood_pressure}   '
        'PR: {pulse_rate}   RR: {respiratory_rate}\n\n'
        'Remarks:\n{remarks}'
    ),
}


def update_body_text(apps, schema_editor):
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')

    for cert_type, body_text in BODY_TEXTS.items():
        CertificateTemplateText.objects.update_or_create(
            certificate_type=cert_type,
            slot_key='body',
            defaults={'text': body_text},
        )


def reverse_update(apps, schema_editor):
    """Restore original body text from the old slot-based templates."""
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')

    # Restore standard
    standard_parts = [
        'This is to certify that {patient_name}, {age} years of age, '
        '{sex}, {college_info}was examined and treated at this clinic on {exam_date}.',
        'Diagnosis: {diagnosis}',
        'The patient is advised to rest from {rest_from} to {rest_to}.',
        'This certificate is issued upon the request of the patient for '
        'whatever legal purpose it may serve.',
    ]
    CertificateTemplateText.objects.update_or_create(
        certificate_type='standard',
        slot_key='body',
        defaults={'text': '\n\n'.join(standard_parts)},
    )

    # Restore fit_to_work
    ftw_parts = [
        'This is to certify that {patient_name}, {age} years of age, '
        '{sex}, {position_info}has been examined and found to be PHYSICALLY FIT '
        'to return to work.',
        'Findings: {diagnosis}',
        'This certificate is issued upon the request of the patient for whatever '
        'legal purpose it may serve.',
    ]
    CertificateTemplateText.objects.update_or_create(
        certificate_type='fit_to_work',
        slot_key='body',
        defaults={'text': '\n\n'.join(ftw_parts)},
    )

    # Restore fit_to_play
    ftp_parts = [
        'This is to certify that {patient_name}, {age} years of age, '
        '{sex}, {college_info}has been examined and found to be PHYSICALLY FIT '
        'to participate in:',
        'Findings: {diagnosis}',
        'This certificate is issued upon the request of the patient for whatever '
        'legal purpose it may serve.',
    ]
    CertificateTemplateText.objects.update_or_create(
        certificate_type='fit_to_play',
        slot_key='body',
        defaults={'text': '\n\n'.join(ftp_parts)},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0013_add_place_field'),
    ]

    operations = [
        migrations.RunPython(update_body_text, reverse_update),
    ]
