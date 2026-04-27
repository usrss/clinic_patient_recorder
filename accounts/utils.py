"""
Utility functions for bulk importing Patient records from Excel files.

Key differences from the old StudentProfile import:
- Creates patients.Patient records (not auth Users)
- birthday is NOT in the import — patients enter it themselves via profile setup
- college is matched by abbreviation against the colleges.College table
- patient_id uniqueness is enforced; existing records are skipped
"""
import pandas as pd
from django.db import transaction

from patients.models import Patient, PatientProfile
from colleges.models import College


class PatientImportError(Exception):
    pass


def validate_excel_structure(df):
    required = {'id', 'first_name', 'last_name', 'sex'}
    missing = required - set(df.columns)
    if missing:
        raise PatientImportError(
            f'Missing required columns: {", ".join(sorted(missing))}'
        )
    return True


def _str_or_empty(value):
    if value is None:
        return ''
    try:
        if pd.isna(value):
            return ''
    except (TypeError, ValueError):
        pass
    result = str(value).strip()
    return '' if result.lower() == 'nan' else result


def clean_row_data(row, college_cache):
    patient_id = _str_or_empty(row.get('id'))
    first_name = _str_or_empty(row.get('first_name'))
    middle_name = _str_or_empty(row.get('middle_name'))
    last_name = _str_or_empty(row.get('last_name'))
    sex = _str_or_empty(row.get('sex')).upper()
    college_abbr = _str_or_empty(row.get('college')).upper()

    if not patient_id:
        raise PatientImportError('id is required and cannot be empty')
    if not first_name:
        raise PatientImportError(f'first_name is required for {patient_id}')
    if not last_name:
        raise PatientImportError(f'last_name is required for {patient_id}')

    sex_map = {'M': 'M', 'MALE': 'M', 'F': 'F', 'FEMALE': 'F'}
    sex = sex_map.get(sex, '')
    if not sex:
        raise PatientImportError(f'sex must be M or F for {patient_id}')

    college = None
    if college_abbr:
        if college_abbr not in college_cache:
            try:
                college_cache[college_abbr] = College.objects.get(abbreviation__iexact=college_abbr)
            except College.DoesNotExist:
                college_cache[college_abbr] = None
        college = college_cache[college_abbr]

    return {
        'patient_id': patient_id,
        'first_name': first_name,
        'middle_name': middle_name,
        'last_name': last_name,
        'sex': sex,
        'college': college,
    }


@transaction.atomic
def import_patients_from_excel(file_obj):
    """
    Read Excel file and create Patient records.
    birthday is NOT imported; patients enter it via profile setup.

    Returns dict: created, skipped, errors, warnings.
    """
    results = {'created': 0, 'skipped': 0, 'errors': [], 'warnings': []}
    college_cache = {}

    try:
        df = pd.read_excel(file_obj, sheet_name=0)
        df.columns = [str(c).strip().lower() for c in df.columns]
        validate_excel_structure(df)

        for idx, row in df.iterrows():
            row_num = idx + 2
            try:
                data = clean_row_data(row, college_cache)
                patient_id = data['patient_id']

                if Patient.objects.filter(patient_id=patient_id).exists():
                    results['skipped'] += 1
                    results['warnings'].append(
                        f'Row {row_num}: Patient {patient_id} already exists (skipped)'
                    )
                    continue

                patient = Patient.objects.create(
                    patient_id=patient_id,
                    first_name=data['first_name'],
                    middle_name=data['middle_name'],
                    last_name=data['last_name'],
                    sex=data['sex'],
                    college=data['college'],
                )
                # Create empty profile — birthday set by patient separately
                PatientProfile.objects.create(patient=patient)

                results['created'] += 1

            except PatientImportError as e:
                results['errors'].append(f'Row {row_num}: {str(e)}')
            except Exception as e:
                results['errors'].append(f'Row {row_num}: Unexpected error — {str(e)}')

        return results

    except pd.errors.EmptyDataError:
        raise PatientImportError('Excel file is empty')
    except PatientImportError:
        raise
    except Exception as e:
        raise PatientImportError(f'Failed to read Excel file: {str(e)}')