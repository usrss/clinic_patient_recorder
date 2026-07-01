from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import AuditLog
from .services import (
    log_audit_entry, log_change, log_create, log_delete,
    log_view, log_auth_event, log_export,
)
from .forms import AuditLogFilterForm

User = get_user_model()


class AuditLogModelTest(TestCase):
    """Test the AuditLog model constraints."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            role='admin',
            first_name='Test',
            last_name='Admin',
        )

    def test_create_audit_log(self):
        log = AuditLog.objects.create(
            user=self.user,
            user_role='admin',
            user_name='Test Admin',
            action='CREATE',
            module='Patients',
            description='Created patient record',
            object_model='patients.Patient',
            object_id='123',
            object_repr='Juan Dela Cruz (123)',
            status='SUCCESS',
        )
        self.assertEqual(log.action, 'CREATE')
        self.assertEqual(log.module, 'Patients')
        self.assertEqual(log.status, 'SUCCESS')
        self.assertIsNotNone(log.pk)
        self.assertIsNotNone(log.timestamp)

    def test_append_only_update_raises(self):
        log = AuditLog.objects.create(
            user=self.user,
            user_role='admin',
            action='CREATE',
            module='Patients',
        )
        with self.assertRaises(RuntimeError):
            log.description = 'modified'
            log.save()

    def test_append_only_delete_raises(self):
        log = AuditLog.objects.create(
            user=self.user,
            user_role='admin',
            action='CREATE',
            module='Patients',
        )
        with self.assertRaises(RuntimeError):
            log.delete()

    def test_bulk_create_immutable_with_pk_raises(self):
        log = AuditLog(
            user=self.user, user_role='admin',
            action='CREATE', module='Patients',
        )
        # Simulate that the object has a pk by setting one
        log.pk = 9999
        with self.assertRaises(RuntimeError):
            AuditLog.bulk_create_immutable([log])

    def test_bulk_create_immutable_works(self):
        logs = [
            AuditLog(
                user=self.user, user_role='admin',
                action='CREATE', module='Patients',
                description=f'Test log {i}',
            )
            for i in range(3)
        ]
        created = AuditLog.bulk_create_immutable(logs)
        self.assertEqual(len(created), 3)

    def test_str_representation(self):
        log = AuditLog.objects.create(
            user=self.user,
            user_role='admin',
            action='LOGIN',
            module='Authentication',
        )
        str_repr = str(log)
        self.assertIn('LOGIN', str_repr)
        self.assertIn('Authentication', str_repr)

    def test_default_status_is_success(self):
        log = AuditLog.objects.create(
            user=self.user,
            user_role='admin',
            action='VIEW',
            module='Reports',
        )
        self.assertEqual(log.status, 'SUCCESS')

    def test_ordering_newest_first(self):
        import datetime
        from django.utils import timezone

        log1 = AuditLog.objects.create(
            user=self.user, user_role='admin',
            action='CREATE', module='Patients',
        )
        log2 = AuditLog.objects.create(
            user=self.user, user_role='admin',
            action='CREATE', module='Consultations',
        )
        logs = AuditLog.objects.all()
        self.assertEqual(logs[0], log2)
        self.assertEqual(logs[1], log1)


class AuditLogServiceTest(TestCase):
    """Test the reusable audit logging service functions."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='doctor1',
            password='testpass123',
            role='doctor',
            first_name='Maria',
            last_name='Santos',
        )
        cls.factory = RequestFactory()

    def test_log_audit_entry(self):
        request = self.factory.get('/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        log_audit_entry(
            user=self.user,
            action='CREATE',
            module='Patients',
            description='Created patient record',
            object_model='patients.Patient',
            object_id='456',
            object_repr='Patient Name',
            request=request,
        )

        log_entry = AuditLog.objects.first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.action, 'CREATE')
        self.assertEqual(log_entry.ip_address, '192.168.1.1')
        self.assertEqual(log_entry.user_name, 'Maria Santos')

    def test_log_change(self):
        request = self.factory.get('/')
        request.user = self.user

        log_change(
            user=self.user,
            module='Consultations',
            description='Updated diagnosis',
            object_model='consultations.Consultation',
            object_id='789',
            changes_before={'diagnosis': 'Common Cold'},
            changes_after={'diagnosis': 'Acute Respiratory Infection'},
            request=request,
        )

        log_entry = AuditLog.objects.first()
        self.assertEqual(log_entry.action, 'UPDATE')
        self.assertEqual(log_entry.changes_before, {'diagnosis': 'Common Cold'})

    def test_log_create(self):
        log_create(
            user=self.user,
            module='Patients',
            description='Created new patient record',
            object_model='patients.Patient',
            object_id='101',
            object_repr='New Patient',
        )

        log_entry = AuditLog.objects.first()
        self.assertEqual(log_entry.action, 'CREATE')

    def test_log_delete(self):
        log_delete(
            user=self.user,
            module='Patients',
            description='Deleted patient record',
            object_model='patients.Patient',
            object_id='202',
            changes_before={'is_active': True},
        )

        log_entry = AuditLog.objects.first()
        self.assertEqual(log_entry.action, 'DELETE')

    def test_log_view(self):
        log_view(
            user=self.user,
            module='Patients',
            description='Viewed patient record',
            object_model='patients.Patient',
            object_id='303',
        )

        log_entry = AuditLog.objects.first()
        self.assertEqual(log_entry.action, 'VIEW')

    def test_log_auth_event(self):
        log_auth_event(
            user=self.user,
            action='LOGIN',
            description='Successful login',
            status='SUCCESS',
        )

        log_entry = AuditLog.objects.first()
        self.assertEqual(log_entry.action, 'LOGIN')
        self.assertEqual(log_entry.module, 'Authentication')

    def test_log_export(self):
        log_export(
            user=self.user,
            module='Reports',
            description='Exported disease report as PDF',
            object_model='reports.DiseaseReport',
        )

        log_entry = AuditLog.objects.first()
        self.assertEqual(log_entry.action, 'EXPORT')

    def test_log_without_request(self):
        log_create(
            user=self.user,
            module='Consultations',
            description='No request provided',
        )
        log_entry = AuditLog.objects.first()
        self.assertIsNotNone(log_entry)
        self.assertIsNone(log_entry.ip_address)

    def test_log_with_unauthenticated_user(self):
        anon_user = type('AnonUser', (), {
            'is_authenticated': False, 'role': '', 'username': ''
        })()
        log_view(user=anon_user, module='Patients', description='Anonymous access')

        log_entry = AuditLog.objects.first()
        self.assertIsNone(log_entry.user)
        self.assertEqual(log_entry.user_role, '')


class AuditLogFilterFormTest(TestCase):
    """Test the audit log filter form."""

    def test_form_valid_empty(self):
        form = AuditLogFilterForm({})
        self.assertTrue(form.is_valid())

    def test_form_with_invalid_date(self):
        form = AuditLogFilterForm({'date_from': 'not-a-date'})
        self.assertTrue(form.is_valid())  # dates are not required

    def test_form_with_valid_data(self):
        form = AuditLogFilterForm({
            'action': 'CREATE',
            'module': 'Patients',
            'status': 'SUCCESS',
        })
        self.assertTrue(form.is_valid())
