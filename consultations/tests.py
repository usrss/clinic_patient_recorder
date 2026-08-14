from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError

from accounts.models import User
from patients.models import Patient, PatientProfile
from inventory.models import Medicine
from audit_logs.models import AuditLog

from .models import Consultation, Prescription, PrescriptionItem


class SingleActiveConsultationTests(TestCase):
    """
    A patient may only have ONE active consultation at a time.

    Active statuses (block new submissions): pending, queued, scheduled,
    triaged, active_follow_up. Closed statuses (patient may submit again
    immediately): completed, cancelled, closed.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='P-100',
            password='secret12345',
            role=User.Role.PATIENT,
        )
        self.patient = Patient.objects.create(
            patient_id='P-100',
            first_name='Ana',
            last_name='Santos',
            sex=Patient.Sex.FEMALE,
        )
        PatientProfile.objects.create(patient=self.patient, profile_completed=True)
        self.client.force_login(self.user)

    def _create_consultation(self, status=Consultation.Status.PENDING):
        return Consultation.objects.create(
            patient=self.patient,
            symptoms='Fever and sore throat',
            severity_description='Moderate',
            status=status,
            is_original_case=True,
        )

    def _submit_new(self):
        return self.client.post(reverse('consultations:patient_submit'), {
            'complaints': 'Headache',
            'symptoms': 'Headache',
            'severity_description': 'Mild since this morning',
            'medical_history': '',
            'additional_notes': '',
        })

    def test_submitted_complaints_saved_as_chief_complaint(self):
        """The patient-submitted form's Complaints field (required) is saved
        as the consultation's chief complaint."""
        response = self.client.post(reverse('consultations:patient_submit'), {
            'complaints': 'Fever since last night',
            'symptoms': 'Headache',
            'severity_description': 'Mild since this morning',
            'medical_history': '',
            'additional_notes': '',
        })
        self.assertRedirects(
            response,
            reverse('consultations:patient_home'),
            fetch_redirect_response=False,
        )
        consultation = Consultation.objects.get(patient=self.patient)
        self.assertEqual(consultation.chief_complaint, 'Fever since last night')
        self.assertEqual(consultation.symptoms, 'Headache')

    def test_patient_submit_requires_complaints(self):
        """Patient submission without Complaints is rejected."""
        response = self.client.post(reverse('consultations:patient_submit'), {
            'symptoms': 'Headache',
            'severity_description': 'Mild',
            'medical_history': '',
            'additional_notes': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Consultation.objects.filter(patient=self.patient).count(), 0)
        self.assertContains(response, 'This field is required')

    def assert_blocked(self, response):
        """The submission is refused and no second consultation is created."""
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Consultation.objects.filter(patient=self.patient).count(), 1)
        self.assertContains(response, 'Active Consultation Exists')

    def assert_allowed(self, response):
        self.assertRedirects(
            response,
            reverse('consultations:patient_home'),
            fetch_redirect_response=False,
        )
        self.assertEqual(Consultation.objects.filter(patient=self.patient).count(), 2)

    # ── Active statuses must block ──────────────────────────────────────────

    def test_pending_blocks_new_consultation(self):
        self._create_consultation(Consultation.Status.PENDING)
        self.assert_blocked(self._submit_new())

    def test_queued_blocks_new_consultation(self):
        self._create_consultation(Consultation.Status.QUEUED)
        self.assert_blocked(self._submit_new())

    def test_scheduled_blocks_new_consultation(self):
        self._create_consultation(Consultation.Status.SCHEDULED)
        self.assert_blocked(self._submit_new())

    def test_triaged_blocks_new_consultation(self):
        """A patient currently being assessed by the nurse/doctor is blocked."""
        self._create_consultation(Consultation.Status.TRIAGED)
        self.assert_blocked(self._submit_new())

    def test_active_follow_up_blocks_new_consultation(self):
        self._create_consultation(Consultation.Status.ACTIVE_FOLLOW_UP)
        self.assert_blocked(self._submit_new())

    # ── Closed statuses must allow a new consultation ───────────────────────

    def test_completed_allows_new_consultation_immediately(self):
        """A patient with a Completed consultation can submit again, even the same day."""
        self._create_consultation(Consultation.Status.COMPLETED)
        self.assert_allowed(self._submit_new())

    def test_cancelled_allows_new_consultation(self):
        self._create_consultation(Consultation.Status.CANCELLED)
        self.assert_allowed(self._submit_new())

    def test_closed_allows_new_consultation(self):
        self._create_consultation(Consultation.Status.CLOSED)
        self.assert_allowed(self._submit_new())

    # ── UX: banner shown, form hidden ───────────────────────────────────────

    def test_submit_page_shows_banner_and_hides_form_when_active(self):
        self._create_consultation(Consultation.Status.PENDING)
        response = self.client.get(reverse('consultations:patient_submit'))
        self.assertContains(response, 'Active Consultation Exists')
        self.assertContains(response, 'View My Consultation')
        self.assertNotContains(response, 'Submit New Consultation')

    # ── Model-level guard (any code path) ───────────────────────────────────

    def test_model_save_blocks_direct_creation_when_active_exists(self):
        self._create_consultation(Consultation.Status.PENDING)
        with self.assertRaises(ValidationError):
            Consultation.objects.create(
                patient=self.patient,
                symptoms='Another concern',
                severity_description='Mild',
                status=Consultation.Status.PENDING,
                is_original_case=True,
            )

    def test_model_save_allows_creation_when_no_active_consultation(self):
        self._create_consultation(Consultation.Status.COMPLETED)
        new = Consultation.objects.create(
            patient=self.patient,
            symptoms='New concern',
            severity_description='Mild',
            status=Consultation.Status.PENDING,
            is_original_case=True,
        )
        self.assertIsNotNone(new.pk)

    def test_active_flag_generated_column(self):
        """The generated `active_flag` column (MySQL-compatible backstop) is 1
        while the consultation is active and NULL once it reaches a closed
        status, so the unique index on (patient, active_flag) allows multiple
        closed consultations but only one active one."""
        active = self._create_consultation(Consultation.Status.PENDING)
        active.refresh_from_db()
        self.assertEqual(active.active_flag, 1)

        active.status = Consultation.Status.COMPLETED
        active.save(update_fields=['status'])
        active.refresh_from_db()
        self.assertIsNone(active.active_flag)

        active.status = Consultation.Status.CANCELLED
        active.save(update_fields=['status'])
        active.refresh_from_db()
        self.assertIsNone(active.active_flag)


class SingleActiveConsultationFrontDeskTests(TestCase):
    """Front desk staff creating consultations on behalf of patients are also
    bound by the single-active-consultation rule."""

    def setUp(self):
        self.staff = User.objects.create_user(
            username='fd1',
            password='secret12345',
            role=User.Role.FRONTDESK,
        )
        self.patient = Patient.objects.create(
            patient_id='P-200',
            first_name='Ben',
            last_name='Cruz',
            sex=Patient.Sex.MALE,
        )
        self.client.force_login(self.staff)

    def _post_create(self):
        return self.client.post(reverse('consultations:consultation_create'), {
            'patient_id': 'P-200',
            'first_name': 'Ben',
            'last_name': 'Cruz',
            'birthdate': '2001-05-10',
            'sex': 'M',
            'contact_number': '',
            'complaints': 'Headache since morning',
            'symptoms': 'Cough and colds',
            'severity_description': 'Moderate',
            'medical_history': '',
            'additional_notes': '',
        })

    def test_frontdesk_blocked_when_patient_has_active_consultation(self):
        Consultation.objects.create(
            patient=self.patient,
            symptoms='Fever',
            severity_description='Mild',
            status=Consultation.Status.PENDING,
            is_original_case=True,
        )
        response = self._post_create()
        self.assertRedirects(
            response,
            reverse('consultations:consultation_create'),
            fetch_redirect_response=False,
        )
        self.assertEqual(Consultation.objects.filter(patient=self.patient).count(), 1)

    def test_frontdesk_allowed_when_patient_has_no_active_consultation(self):
        response = self._post_create()
        self.assertRedirects(
            response,
            reverse('consultations:queue'),
            fetch_redirect_response=False,
        )
        self.assertEqual(Consultation.objects.filter(patient=self.patient).count(), 1)

    def test_frontdesk_allowed_after_consultation_completed(self):
        Consultation.objects.create(
            patient=self.patient,
            symptoms='Fever',
            severity_description='Mild',
            status=Consultation.Status.COMPLETED,
            is_original_case=True,
        )
        response = self._post_create()
        self.assertRedirects(
            response,
            reverse('consultations:queue'),
            fetch_redirect_response=False,
        )
        self.assertEqual(Consultation.objects.filter(patient=self.patient).count(), 2)


class AdminReopenSingleActiveTests(TestCase):
    """Admin reopening a cancelled consultation must not create a second
    active consultation for the patient."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='adm1',
            password='secret12345',
            role=User.Role.ADMIN,
        )
        self.patient = Patient.objects.create(
            patient_id='P-300',
            first_name='Cleo',
            last_name='Reyes',
            sex=Patient.Sex.FEMALE,
        )
        self.client.force_login(self.admin)

    def test_reopen_blocked_when_patient_has_other_active_consultation(self):
        cancelled = Consultation.objects.create(
            patient=self.patient,
            symptoms='Old concern',
            severity_description='Mild',
            status=Consultation.Status.CANCELLED,
            is_original_case=True,
        )
        Consultation.objects.create(
            patient=self.patient,
            symptoms='Current concern',
            severity_description='Mild',
            status=Consultation.Status.PENDING,
            is_original_case=True,
        )
        response = self.client.post(
            reverse('consultations:admin_reopen', args=[cancelled.pk])
        )
        self.assertRedirects(
            response,
            reverse('consultations:queue'),
            fetch_redirect_response=False,
        )
        cancelled.refresh_from_db()
        self.assertEqual(cancelled.status, Consultation.Status.CANCELLED)

    def test_reopen_allowed_when_no_other_active(self):
        cancelled = Consultation.objects.create(
            patient=self.patient,
            symptoms='Old concern',
            severity_description='Mild',
            status=Consultation.Status.CANCELLED,
            is_original_case=True,
        )
        response = self.client.post(
            reverse('consultations:admin_reopen', args=[cancelled.pk])
        )
        self.assertRedirects(
            response,
            reverse('consultations:queue'),
            fetch_redirect_response=False,
        )
        cancelled.refresh_from_db()
        self.assertEqual(cancelled.status, Consultation.Status.PENDING)


class PrescriptionEditTests(TestCase):
    """
    Doctors may edit an existing prescription while the consultation is still
    open (TRIAGED). Edits are audit-logged and inventory stock is returned
    for removed/reduced medicines and re-deducted for the final list.
    """

    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doc_edit', password='secret12345', role=User.Role.DOCTOR,
        )
        self.patient = Patient.objects.create(
            patient_id='P-400',
            first_name='Dora',
            last_name='Miles',
            sex=Patient.Sex.FEMALE,
        )
        PatientProfile.objects.create(patient=self.patient, profile_completed=True)
        self.client.force_login(self.doctor)

    def _make_consultation(self, status=Consultation.Status.TRIAGED, with_prescription=True):
        consultation = Consultation.objects.create(
            patient=self.patient,
            symptoms='Headache',
            severity_description='Mild',
            status=status,
            is_original_case=True,
        )
        prescription = None
        if with_prescription:
            prescription = Prescription.objects.create(
                consultation=consultation,
                doctor=self.doctor,
                diagnosis='Migraine',
                treatment_plan='Rest',
            )
        return consultation, prescription

    def _inventory_row(self, med, qty, dosage='500mg', freq='3x a day', dur='7 days'):
        return {
            'meds-0-source': 'inventory',
            'meds-0-medicine': str(med.pk),
            'meds-0-inv_dosage': dosage,
            'meds-0-inv_frequency': freq,
            'meds-0-inv_duration': dur,
            'meds-0-quantity': str(qty),
            'meds-0-inv_instructions': '',
        }

    def _post_data(self, diagnosis='Tension headache', treatment_plan='Hydrate', row=None):
        data = {
            'diagnosis': diagnosis,
            'treatment_plan': treatment_plan,
            'meds-TOTAL_FORMS': '1',
            'meds-INITIAL_FORMS': '0',
            'meds-MIN_NUM_FORMS': '0',
            'meds-MAX_NUM_FORMS': '1000',
        }
        if row:
            data.update(row)
        return data

    def test_edit_updates_diagnosis_items_and_redirects(self):
        consultation, prescription = self._make_consultation()
        med = Medicine.objects.create(name='Paracetamol', quantity=100, unit=Medicine.Unit.TABLET)
        PrescriptionItem.objects.create(
            prescription=prescription, medicine=med, medicine_name='Paracetamol',
            quantity=10, dosage='500mg', frequency='3x a day', duration='7 days',
        )

        response = self.client.post(
            reverse('consultations:prescription_edit', args=[consultation.pk]),
            self._post_data(row=self._inventory_row(med, 5)),
        )
        self.assertRedirects(
            response,
            reverse('consultations:consultation_complete', args=[consultation.pk]),
            fetch_redirect_response=False,
        )

        prescription.refresh_from_db()
        self.assertEqual(prescription.diagnosis, 'Tension headache')
        self.assertEqual(prescription.treatment_plan, 'Hydrate')
        items = list(prescription.items.all())
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].medicine, med)
        self.assertEqual(items[0].dosage, '500mg')
        self.assertEqual(items[0].frequency, '3x a day')
        self.assertEqual(items[0].duration, '7 days')

    def test_edit_restores_and_rededucts_inventory_stock(self):
        """Removing/reducing a medicine returns its stock to inventory."""
        consultation, prescription = self._make_consultation()
        med = Medicine.objects.create(name='Paracetamol', quantity=100, unit=Medicine.Unit.TABLET)
        PrescriptionItem.objects.create(
            prescription=prescription, medicine=med, medicine_name='Paracetamol',
            quantity=10, dosage='500mg', frequency='3x a day', duration='7 days',
        )
        # Simulate the original dispensing during create
        med.deduct_stock(10)
        med.refresh_from_db()
        self.assertEqual(med.quantity, 90)

        # Reduce quantity 10 → 3
        response = self.client.post(
            reverse('consultations:prescription_edit', args=[consultation.pk]),
            self._post_data(row=self._inventory_row(med, 3)),
        )
        self.assertRedirects(
            response,
            reverse('consultations:consultation_complete', args=[consultation.pk]),
            fetch_redirect_response=False,
        )

        med.refresh_from_db()
        self.assertEqual(med.quantity, 97)  # 90 + 10 restored − 3 re-deducted

    def test_edit_is_audit_logged_with_before_after(self):
        consultation, prescription = self._make_consultation()
        med = Medicine.objects.create(name='Paracetamol', quantity=100, unit=Medicine.Unit.TABLET)
        PrescriptionItem.objects.create(
            prescription=prescription, medicine=med, medicine_name='Paracetamol',
            quantity=10, dosage='500mg', frequency='3x a day', duration='7 days',
        )

        response = self.client.post(
            reverse('consultations:prescription_edit', args=[consultation.pk]),
            self._post_data(row=self._inventory_row(med, 4)),
        )
        self.assertEqual(response.status_code, 302)

        entry = AuditLog.objects.filter(
            action='UPDATE',
            module='Consultations',
            object_model='consultations.Prescription',
            object_id=str(prescription.pk),
        ).order_by('-id').first()
        self.assertIsNotNone(entry)
        self.assertIn('Amended prescription', entry.description)
        self.assertEqual(entry.changes_before['diagnosis'], 'Migraine')
        self.assertEqual(entry.changes_after['diagnosis'], 'Tension headache')
        self.assertEqual(entry.changes_before['items'][0]['name'], 'Paracetamol')
        self.assertEqual(entry.changes_before['items'][0]['dosage'], '500mg')
        self.assertEqual(entry.changes_after['items'][0]['dosage'], '500mg')
        self.assertEqual(entry.changes_after['items'][0]['name'], 'Paracetamol')

    def test_edit_blocked_after_consultation_completed(self):
        """A completed consultation's prescription can no longer be edited."""
        consultation, _ = self._make_consultation(status=Consultation.Status.COMPLETED)
        response = self.client.get(
            reverse('consultations:prescription_edit', args=[consultation.pk])
        )
        self.assertRedirects(
            response,
            reverse('consultations:clinical_detail', args=[consultation.pk]),
            fetch_redirect_response=False,
        )

    def test_edit_restores_stock_for_items_created_by_real_prescribe_flow(self):
        """Regression: prescriptions created through the actual prescribe view
        must persist the dispensed quantity on each item, otherwise a later edit
        cannot restore the correct stock."""
        consultation, _ = self._make_consultation(with_prescription=False)
        med = Medicine.objects.create(name='Amoxicillin', quantity=50, unit=Medicine.Unit.CAPSULE)

        # Create the prescription through the real prescribe flow (10 units)
        response = self.client.post(
            reverse('consultations:prescribe', args=[consultation.pk]),
            self._post_data(row=self._inventory_row(med, 10)),
        )
        self.assertRedirects(
            response,
            reverse('consultations:consultation_complete', args=[consultation.pk]),
            fetch_redirect_response=False,
        )
        med.refresh_from_db()
        self.assertEqual(med.quantity, 40)
        prescription = consultation.prescriptions.first()
        item = prescription.items.first()
        self.assertEqual(item.quantity, 10)  # quantity must be persisted

        # Edit it down to 3 units — the previously dispensed 10 must be
        # restored before the new 3 are deducted: 40 + 10 − 3 = 47.
        response = self.client.post(
            reverse('consultations:prescription_edit', args=[consultation.pk]),
            self._post_data(row=self._inventory_row(med, 3)),
        )
        self.assertRedirects(
            response,
            reverse('consultations:consultation_complete', args=[consultation.pk]),
            fetch_redirect_response=False,
        )
        med.refresh_from_db()
        self.assertEqual(med.quantity, 47)
        prescription.refresh_from_db()
        item = prescription.items.first()
        self.assertEqual(item.quantity, 3)

    def test_edit_requires_existing_prescription(self):
        consultation, _ = self._make_consultation(with_prescription=False)
        response = self.client.get(
            reverse('consultations:prescription_edit', args=[consultation.pk])
        )
        self.assertRedirects(
            response,
            reverse('consultations:prescribe', args=[consultation.pk]),
            fetch_redirect_response=False,
        )

    def test_edit_page_prefills_existing_custom_item(self):
        """GET renders the form with the existing medicine rows pre-filled."""
        consultation, prescription = self._make_consultation()
        PrescriptionItem.objects.create(
            prescription=prescription, medicine=None, medicine_name='Betadine Gargle',
            dosage='10ml', frequency='2x a day', duration='5 days', instructions='Gargle after meals',
        )

        response = self.client.get(
            reverse('consultations:prescription_edit', args=[consultation.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Betadine Gargle')
        self.assertContains(response, 'Edit Prescription')

    def test_create_prescribe_page_still_renders(self):
        """The create (non-edit) prescribe page still renders after the
        edit-mode template changes."""
        consultation, _ = self._make_consultation(with_prescription=False)
        response = self.client.get(
            reverse('consultations:prescribe', args=[consultation.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save & Complete')
        self.assertContains(response, 'From Inventory')


class PatientConsultationSubmitTests(TestCase):
    def test_patient_can_submit_new_consultation_without_submit_button_name(self):
        user = User.objects.create_user(
            username='P-002',
            password='secret12345',
            role=User.Role.PATIENT,
        )
        patient = Patient.objects.create(
            patient_id='P-002',
            first_name='Patient',
            last_name='Two',
            sex=Patient.Sex.MALE,
        )
        PatientProfile.objects.create(patient=patient, profile_completed=True)
        self.client.force_login(user)

        response = self.client.post(reverse('consultations:patient_submit'), {
            'complaints': 'Fever and sore throat',
            'symptoms': 'Fever and sore throat',
            'severity_description': 'Moderate fever since last night',
            'medical_history': '',
            'additional_notes': 'No other notes',
        })

        self.assertRedirects(
            response,
            reverse('consultations:patient_home'),
            fetch_redirect_response=False,
        )
        consultation = Consultation.objects.get(patient=patient)
        self.assertEqual(consultation.chief_complaint, 'Fever and sore throat')
        self.assertEqual(consultation.symptoms, 'Fever and sore throat')
        self.assertEqual(
            consultation.severity_description,
            'Moderate fever since last night',
        )
        self.assertEqual(consultation.status, Consultation.Status.PENDING)
        self.assertTrue(consultation.is_original_case)


class TriageChiefComplaintTests(TestCase):
    """
    Doctor-review step for the chief complaint during triage.
    The field is required and prefilled with the patient's own words, so the
    doctor must explicitly confirm/reword it. The saved value is what appears
    on official documents (print form, medical history).
    """

    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doc1',
            password='secret12345',
            role=User.Role.DOCTOR,
        )
        self.patient = Patient.objects.create(
            patient_id='P-003',
            first_name='Jane',
            last_name='Doe',
            sex=Patient.Sex.FEMALE,
        )
        self.consultation = Consultation.objects.create(
            patient=self.patient,
            symptoms='sakit ako tiyan po',
            severity_description='Since last night',
            status=Consultation.Status.QUEUED,
            is_original_case=True,
        )
        self.client.force_login(self.doctor)

    def _post_triage(self, chief_complaint):
        return self.client.post(
            reverse('consultations:triage_form', args=[self.consultation.pk]),
            {
                'chief_complaint': chief_complaint,
                'blood_pressure': '120/80',
                'temperature': '36.5',
                'pulse_rate': '72',
                'hypertension': 'on',
                'diabetes': '',
                'asthma': '',
                'cardiac_problems': '',
                'arthritis': '',
                'other_conditions': '',
                'bcg': '',
                'dpt': '',
                'opv': '',
                'hepatitis_b': '',
                'measles': '',
                'tt': '',
            },
        )

    def test_triage_saves_doctors_reviewed_chief_complaint(self):
        response = self._post_triage('abdominal pain for 2 days')
        self.assertRedirects(
            response,
            reverse('consultations:prescribe', args=[self.consultation.pk]),
            fetch_redirect_response=False,
        )
        self.consultation.refresh_from_db()
        self.assertEqual(
            self.consultation.chief_complaint,
            'abdominal pain for 2 days',
        )
        self.assertEqual(self.consultation.status, Consultation.Status.TRIAGED)

    def test_triage_requires_chief_complaint(self):
        """The doctor must explicitly confirm/reword the chief complaint —
        a blank value blocks the triage from being saved."""
        response = self._post_triage('')
        self.assertEqual(response.status_code, 200)  # re-renders with errors
        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.status, Consultation.Status.QUEUED)
        self.assertFalse(self.consultation.triages.exists())
        self.assertFormError(
            response.context['form'],
            'chief_complaint',
            'This field is required.',
        )

    def test_triage_form_prefills_patient_words(self):
        response = self.client.get(
            reverse('consultations:triage_form', args=[self.consultation.pk])
        )
        form = response.context['form']
        self.assertEqual(form.initial['chief_complaint'], 'sakit ako tiyan po')

    def test_triage_edit_blocked_after_prescription(self):
        """Once a prescription exists, the triage record can no longer be
        amended — amendment is only allowed BEFORE prescribing."""
        from .models import Prescription, Triage

        self.consultation.status = Consultation.Status.TRIAGED
        self.consultation.save(update_fields=['status'])
        Triage.objects.create(
            consultation=self.consultation,
            blood_pressure='120/80',
            temperature=36.5,
            pulse_rate=72,
        )
        Prescription.objects.create(
            consultation=self.consultation,
            doctor=self.doctor,
            diagnosis='Abdominal pain',
        )

        response = self.client.get(
            reverse('consultations:triage_edit', args=[self.consultation.pk])
        )
        self.assertRedirects(
            response,
            reverse('consultations:triage_list'),
            fetch_redirect_response=False,
        )

    def test_triage_amendment_is_audit_logged(self):
        """Amending a triage must create an audit log entry (UPDATE action)
        so the change is traceable in the audit trail."""
        from .models import Triage
        from audit_logs.models import AuditLog

        self.consultation.status = Consultation.Status.TRIAGED
        self.consultation.save(update_fields=['status'])
        Triage.objects.create(
            consultation=self.consultation,
            blood_pressure='120/80',
            temperature=36.5,
            pulse_rate=72,
        )

        response = self.client.post(
            reverse('consultations:triage_edit', args=[self.consultation.pk]),
            {
                'blood_pressure': '130/85',
                'temperature': '36.6',
                'pulse_rate': '74',
                'notes': '',
                'chief_complaint': 'abdominal pain',
                'amendment_reason': 'Re-measured blood pressure',
            },
        )
        self.assertRedirects(
            response,
            reverse('consultations:triage_list'),
            fetch_redirect_response=False,
        )

        entry = AuditLog.objects.filter(
            action='UPDATE',
            module='Consultations',
            object_id=str(self.consultation.pk),
        ).order_by('-id').first()
        self.assertIsNotNone(entry)
        self.assertIn('Amended triage', entry.description)
        self.assertEqual(entry.changes_after['chief_complaint'], 'abdominal pain')


class FrontDeskComplaintsFieldTest(TestCase):
    """The optional Complaints field on the front-desk intake form is saved
    as the consultation's chief complaint, so certificates can show the
    patient's complaint separately from the diagnosis (assessment)."""

    def setUp(self):
        self.staff = User.objects.create_user(
            username='fd_complaints',
            password='secret12345',
            role=User.Role.FRONTDESK,
        )
        self.patient = Patient.objects.create(
            patient_id='P-COMPLAINTS',
            first_name='Liza',
            last_name='Tan',
            sex=Patient.Sex.FEMALE,
        )
        self.client.force_login(self.staff)

    def test_complaints_field_saved_as_chief_complaint(self):
        response = self.client.post(reverse('consultations:consultation_create'), {
            'patient_id': 'P-COMPLAINTS',
            'first_name': 'Liza',
            'last_name': 'Tan',
            'birthdate': '2002-03-15',
            'sex': 'F',
            'contact_number': '',
            'complaints': 'Headache since morning',
            'symptoms': 'Cough and colds',
            'severity_description': 'Moderate',
            'medical_history': '',
            'additional_notes': '',
        })
        self.assertRedirects(response, reverse('consultations:queue'), fetch_redirect_response=False)
        consultation = Consultation.objects.get(patient=self.patient)
        self.assertEqual(consultation.chief_complaint, 'Headache since morning')
        self.assertEqual(consultation.symptoms, 'Cough and colds')

    def test_complaints_is_required(self):
        """Complaints is required on the walk-in intake form — omitting it
        re-renders the form with an error and creates no consultation."""
        response = self.client.post(reverse('consultations:consultation_create'), {
            'patient_id': 'P-COMPLAINTS',
            'first_name': 'Liza',
            'last_name': 'Tan',
            'birthdate': '2002-03-15',
            'sex': 'F',
            'contact_number': '',
            'symptoms': 'Cough and colds',
            'severity_description': 'Moderate',
            'medical_history': '',
            'additional_notes': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Consultation.objects.filter(patient=self.patient).count(), 0)
        self.assertContains(response, 'This field is required')

    def test_symptoms_and_severity_are_optional(self):
        """A walk-in consultation can be created with only Complaints filled."""
        response = self.client.post(reverse('consultations:consultation_create'), {
            'patient_id': 'P-COMPLAINTS',
            'first_name': 'Liza',
            'last_name': 'Tan',
            'birthdate': '2002-03-15',
            'sex': 'F',
            'contact_number': '',
            'complaints': 'Headache since morning',
            'symptoms': '',
            'severity_description': '',
            'medical_history': '',
            'additional_notes': '',
        })
        self.assertRedirects(response, reverse('consultations:queue'), fetch_redirect_response=False)
        consultation = Consultation.objects.get(patient=self.patient)
        self.assertEqual(consultation.chief_complaint, 'Headache since morning')
        self.assertEqual(consultation.symptoms, '')
        self.assertEqual(consultation.severity_description, '')
