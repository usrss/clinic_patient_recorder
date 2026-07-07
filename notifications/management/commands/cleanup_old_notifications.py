from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Delete read notifications older than the specified number of days.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete read notifications older than this many days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show how many would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff = timezone.now() - timezone.timedelta(days=days)

        qs = Notification.objects.filter(is_read=True, created_at__lt=cutoff)
        count = qs.count()

        if dry_run:
            self.stdout.write(
                f'[DRY RUN] Would delete {count} read notification(s) '
                f'older than {days} day(s).'
            )
            return

        qs.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {count} read notification(s) older than {days} day(s).'
            )
        )
