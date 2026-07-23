from django.db import migrations


# ── Correct body text for each certificate type ──────────────────────────────
# Each template uses only the placeholders that are relevant to that cert type
# and that have corresponding fields in the step 2 form.

BODY_TEXTS = {
    'absences': (
        'This is to certify that {patient_name}, {age} years old '
        'and a {course} student in this campus, was examined and treated '
        'at this clinic on {exam_date}.\n\n'
        'Diagnosis:\n'
        '• {diagnosis}\n\n'
        'The patient is advised to rest from {rest_from} to {rest_to}.\n\n'
        'Remarks:\n'
        '{remarks}\n\n'
        'Given this {day} day of {month}, {year} at {place}, '
        'for whatever legal purpose it may serve.'
    ),
    'ojt': (
        'This is to certify that {patient_name}, {age} years old '
        'and a {course} student in this campus, has been examined '
        'and found to be PHYSICALLY FIT to return to '
        'On-the-Job Training (OJT).\n\n'
        'Assessment: {work_assessment}\n\n'
        'Findings:\n'
        '• {diagnosis}\n\n'
        'Recommended Return Date: {return_date}\n\n'
        'Restrictions/Limitations:\n'
        '{restrictions}\n\n'
        'Given this {day} day of {month}, {year} at {place}, '
        'for whatever legal purpose it may serve.\n\n'
        'Remarks:\n'
        '{remarks}'
    ),
    'activities': (
        'This is to certify that {patient_name}, {age} years old '
        'and a {course} student in this campus, has been examined '
        'and found to be PHYSICALLY FIT to participate in:\n\n'
        '{activity_name}\n\n'
        'Fitness Status: {fitness_status}\n\n'
        'Findings:\n'
        '• {diagnosis}\n\n'
        'Given this {day} day of {month}, {year} at {place}, '
        'for whatever legal purpose it may serve.\n\n'
        'Remarks:\n'
        '{remarks}'
    ),
}


def update_body_texts(apps, schema_editor):
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')

    for cert_type, body_text in BODY_TEXTS.items():
        CertificateTemplateText.objects.update_or_create(
            certificate_type=cert_type,
            slot_key='body',
            defaults={'text': body_text},
        )


def reverse_update(apps, schema_editor):
    """Restore the prior (migration 0014) body texts."""
    old_texts = {
        'absences': (
            'This is to certify that {patient_name}, {age} years old and a '
            '{course} student in this campus, has been consulted '
            'in the clinic, due to the following complaints and assessments.\n\n'
            'Complaint/s:\n• {diagnosis}\n\n'
            'Assessment/s:\n• {diagnosis}\n\n'
            'Remark/s:\n• {remarks}\n\n'
            'Given this {day} day of {month}, {year} at {place}, '
            'for whatever legal purpose this may serve.'
        ),
        'ojt': (
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
        'activities': (
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

    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')
    for cert_type, body_text in old_texts.items():
        CertificateTemplateText.objects.update_or_create(
            certificate_type=cert_type,
            slot_key='body',
            defaults={'text': body_text},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0015_rename_certificate_type_codes'),
    ]

    operations = [
        migrations.RunPython(update_body_texts, reverse_update),
    ]
