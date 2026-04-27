"""
Utility functions for bulk importing students from Excel files.
"""
import pandas as pd
from django.db import transaction
from django.contrib.auth import get_user_model
from accounts.models import StudentProfile

User = get_user_model()


class StudentImportError(Exception):
    """Custom exception for student import errors."""
    pass


def validate_excel_structure(df):
    """
    Validate that the Excel file has required columns.
    Required: student_id, first_name, last_name, age, gender
    Optional: middle_name, college
    """
    required_columns = {'student_id', 'first_name', 'last_name', 'age', 'gender'}
    missing = required_columns - set(df.columns)

    if missing:
        raise StudentImportError(
            f'Missing required columns: {", ".join(sorted(missing))}'
        )

    return True


def _str_or_empty(value):
    """
    FIX: Safely convert a cell value to a stripped string.
    Returns '' for None, NaN, or the literal string 'nan'.
    This prevents falsy-value bugs where valid data like '0' or 'False'
    would be silently dropped by a plain `if row.get('field')` check.
    """
    if value is None:
        return ''
    try:
        if pd.isna(value):
            return ''
    except (TypeError, ValueError):
        pass
    result = str(value).strip()
    return '' if result.lower() == 'nan' else result


def clean_row_data(row):
    """
    Clean and validate a single student row.
    Returns a dict with cleaned data or raises StudentImportError.
    """
    student_id = _str_or_empty(row.get('student_id'))
    first_name = _str_or_empty(row.get('first_name'))
    # FIX: Use _str_or_empty for optional fields instead of `if row.get(...)`,
    # which would silently drop falsy-but-valid strings like '0'.
    middle_name = _str_or_empty(row.get('middle_name'))
    last_name = _str_or_empty(row.get('last_name'))
    age = row.get('age')
    gender = _str_or_empty(row.get('gender')).upper()
    college = _str_or_empty(row.get('college'))

    # Validation
    if not student_id:
        raise StudentImportError('student_id is required and cannot be empty')

    if not first_name:
        raise StudentImportError(f'first_name is required for {student_id}')

    if not last_name:
        raise StudentImportError(f'last_name is required for {student_id}')

    # Validate age
    try:
        if age is not None and not pd.isna(age):
            age = int(age)
            if age < 10 or age > 120:
                raise StudentImportError(f'Age {age} for {student_id} is out of range (10–120)')
        else:
            age = None
    except (ValueError, TypeError):
        age = None

    # Normalize gender
    gender_map = {
        'M': 'M', 'MALE': 'M',
        'F': 'F', 'FEMALE': 'F',
        'O': 'O', 'OTHER': 'O',
    }
    gender = gender_map.get(gender, '')

    return {
        'student_id': student_id,
        'first_name': first_name,
        'middle_name': middle_name,
        'last_name': last_name,
        'age': age,
        'gender': gender,
        'college': college,
    }


@transaction.atomic
def import_students_from_excel(file_obj):
    """
    Read Excel file and create User + StudentProfile for each student.

    Returns a dict with:
    - created: count of newly created users
    - skipped: count of existing users (not recreated)
    - errors: list of error messages
    - warnings: list of warnings
    """
    results = {
        'created': 0,
        'skipped': 0,
        'errors': [],
        'warnings': [],
    }

    try:
        df = pd.read_excel(file_obj, sheet_name=0)
        # FIX: Normalise column names to lowercase/stripped to be tolerant of
        # Excel files where the header row has inconsistent casing or spacing.
        df.columns = [str(c).strip().lower() for c in df.columns]
        validate_excel_structure(df)

        for idx, row in df.iterrows():
            row_num = idx + 2  # Account for header row

            try:
                data = clean_row_data(row)
                student_id = data['student_id']

                # Skip if user already exists
                if User.objects.filter(username=student_id).exists():
                    results['skipped'] += 1
                    results['warnings'].append(
                        f'Row {row_num}: User {student_id} already exists (skipped)'
                    )
                    continue

                # Create User account
                user = User.objects.create_user(
                    username=student_id,
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    password=student_id,        # Default password = student_id
                    role=User.Role.STUDENT,
                    is_active=True,
                    force_password_change=True,  # Force change on first login
                )

                # Create StudentProfile
                StudentProfile.objects.create(
                    user=user,
                    student_id=student_id,
                    middle_name=data['middle_name'],
                    age=data['age'],
                    gender=data['gender'],
                    college=data['college'],
                )

                results['created'] += 1

            except StudentImportError as e:
                results['errors'].append(f'Row {row_num}: {str(e)}')
            except Exception as e:
                results['errors'].append(f'Row {row_num}: Unexpected error — {str(e)}')

        return results

    except pd.errors.EmptyDataError:
        raise StudentImportError('Excel file is empty')
    except StudentImportError:
        raise
    except Exception as e:
        raise StudentImportError(f'Failed to read Excel file: {str(e)}')