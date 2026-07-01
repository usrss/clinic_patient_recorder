"""
Management command that voids draft medical certificates older than 24 hours.

Drafts that were started but never issued accumulate in the database.
This command cleans them up by marking them as voided with a system reason.

Run via cron / scheduler:
    python manage.py cleanup_stale_drafts

Dry-run mode (no changes):
    python manage.py cleanup_stale_drafts --dry-run
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from certificates.models import MedicalCertificate


class Command(BaseCommand):
    help = 'Void draft certificates older than 24 hours (abandoned drafts).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview which drafts would be voided without making changes.',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Age threshold in hours (default: 24).',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        hours = options.get('hours', 24)

        cutoff = timezone.now() - timedelta(hours=hours)

        stale_drafts = MedicalCertificate.objects.filter(
            status=MedicalCertificate.Status.DRAFT,
            created_at__lt=cutoff,
        )

        total = stale_drafts.count()

        self.stdout.write(self.style.NOTICE(
            f'Stale draft threshold:  {hours} hours (before {cutoff.strftime("%Y-%m-%d %H:%M")})\n'
            f'Drafts found:           {total}\n'
            f'Dry run:                {"YES (no changes)" if dry_run else "NO"}\n'
        ))

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No stale drafts to clean up.'))
            return

        for draft in stale_drafts:
            if dry_run:
                self.stdout.write(
                    f'  Would void: Cert #{draft.pk} ({draft.get_certificate_type_display()}) '
                    f'— created {draft.created_at.strftime("%Y-%m-%d %H:%M")} '
                    f'— patient: {draft.patient_name}'
                )
            else:
                draft.status = MedicalCertificate.Status.VOIDED
                draft.save(update_fields=['status'])
                from certificates.models import CertificateAuditLog
                CertificateAuditLog.objects.create(
                    certificate=draft,
                    user=None,
                    action='voided',
                    details='Auto-voided: abandoned draft',
                )

        action = 'Would void' if dry_run else 'Voided'
        self.stdout.write(self.style.SUCCESS(
            f'\nSummary:\n'
            f'  {action}: {total} draft(s)\n'
            f'  Dry run: {dry_run}\n'
        ))
