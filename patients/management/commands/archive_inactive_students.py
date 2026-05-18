"""
Management command that archives students who:
1. Have an expected_graduation_year <= current year (should have graduated)
2. Have no consultations in the last N months (archive_after_months)
3. Have a college set (are actually students)
4. Are not already archived

Run daily via cron / scheduler:
    python manage.py archive_inactive_students

Dry-run mode (no changes):
    python manage.py archive_inactive_students --dry-run
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from patients.models import Patient, AcademicYearSettings


class Command(BaseCommand):
    help = 'Archive students who have graduated and been inactive since academic year end.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview which patients would be archived without making changes.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        # ── Load settings ──────────────────────────────────────────────────
        try:
            settings = AcademicYearSettings.objects.first()
            if settings is None:
                self.stdout.write(self.style.WARNING(
                    'No AcademicYearSettings configured. '
                    'Please set up via admin > Academic Year Settings first.'
                ))
                return
        except AcademicYearSettings.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'AcademicYearSettings model not found. Ensure the app is migrated.'
            ))
            return

        year_end = settings.academic_year_end
        archive_after = settings.archive_after_months

        current_year = timezone.now().year

        # Calculate archive threshold: academic_year_end + archive_after_months
        import calendar
        total_months = year_end.month + archive_after
        target_year = year_end.year + (total_months - 1) // 12
        target_month = ((total_months - 1) % 12) + 1
        max_day = calendar.monthrange(target_year, target_month)[1]
        threshold_date = year_end.replace(
            year=target_year,
            month=target_month,
            day=min(year_end.day, max_day),
        )

        self.stdout.write(self.style.NOTICE(
            f'Academic year end:   {year_end.strftime("%B %d, %Y")}\n'
            f'Archive after:        {archive_after} months\n'
            f'Threshold date:       {threshold_date.strftime("%B %d, %Y")}\n'
            f'Current year:         {current_year}\n'
            f'Dry run:              {"YES (no changes)" if dry_run else "NO"}\n'
        ))

        # ── Find candidates ────────────────────────────────────────────────
        candidates = Patient.objects.filter(
            college__isnull=False,   # Is a student
            expected_graduation_year__lte=current_year,  # Should have graduated
            is_archived=False,       # Not already archived
            is_active=True,          # Still active
        )

        # Further filter: no consultations after the threshold date
        from consultations.models import Consultation

        archived_count = 0
        skipped_no_consultations = 0
        skipped_recent_activity = 0

        for patient in candidates:
            # Check latest consultation
            latest = Consultation.objects.filter(
                patient=patient,
            ).order_by('-created_at').first()

            if latest is None:
                # No consultations at all — still archive (student never visited)
                pass  # Will be archived
            elif latest.created_at.date() >= threshold_date:
                # Has activity after threshold — skip
                skipped_recent_activity += 1
                continue

            reason = 'Graduated — no activity after academic year end'

            if dry_run:
                self.stdout.write(
                    f'  Would archive: {patient.patient_id} — '
                    f'{patient.get_full_name()} (grad yr: {patient.expected_graduation_year})'
                )
            else:
                patient.is_archived = True
                patient.archived_at = timezone.now()
                patient.archived_reason = reason
                patient.save(update_fields=['is_archived', 'archived_at', 'archived_reason'])

            archived_count += 1

        # ── Summary ────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f'\nSummary:\n'
            f'  Patients archived:        {archived_count}\n'
            f'  Skipped (recent activity): {skipped_recent_activity}\n'
            f'  Dry run:                  {dry_run}\n'
        ))
