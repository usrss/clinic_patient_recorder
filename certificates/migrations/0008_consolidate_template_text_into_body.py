from django.db import migrations

# ── Ordered slot keys per certificate type ──────────────────────────────────
SLOT_ORDER = {
    'standard': ['diagnosis_statement', 'diagnosis_line', 'rest_period_single', 'rest_period_range', 'closing_statement'],
    'fit_to_work': ['statement', 'findings_line', 'closing_statement'],
    'fit_to_play': ['statement', 'findings_line', 'closing_statement'],
}


def consolidate_into_body(apps, schema_editor):
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')

    for cert_type, keys in SLOT_ORDER.items():
        # Fetch all existing slots for this type
        slots = {
            s.slot_key: s.text
            for s in CertificateTemplateText.objects.filter(certificate_type=cert_type)
        }

        # Build combined body text
        parts = []
        for key in keys:
            text = slots.get(key)
            if text and text.strip():
                parts.append(text.strip())

        body_text = '\n\n'.join(parts)

        # Create or update the 'body' entry
        CertificateTemplateText.objects.update_or_create(
            certificate_type=cert_type,
            slot_key='body',
            defaults={'text': body_text},
        )

        # Delete old slot entries for this type
        CertificateTemplateText.objects.filter(
            certificate_type=cert_type,
        ).exclude(slot_key='body').delete()


def reverse_consolidation(apps, schema_editor):
    CertificateTemplateText = apps.get_model('certificates', 'CertificateTemplateText')

    for cert_type, keys in SLOT_ORDER.items():
        body = CertificateTemplateText.objects.filter(
            certificate_type=cert_type, slot_key='body'
        ).first()
        if not body:
            continue

        # We cannot reliably split body text back into individual slots,
        # so we delete the body entry and leave it to the seed migrations
        # to repopulate (0006, 0007).
        body.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0007_seed_closing_statement'),
    ]

    operations = [
        migrations.RunPython(consolidate_into_body, reverse_consolidation),
    ]
