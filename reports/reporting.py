"""
Shared reporting definitions for the Reports module.

This module is the single source of truth for how report numbers are
computed. Web pages, CSV, Excel, and PDF exports must all derive their
figures from these helpers so the same filters always produce the same
numbers everywhere.

COUNTING UNITS
--------------
- "Diagnosis case"    One COMPLETED consultation that carries the diagnosis.
                      Several prescriptions of the same diagnosis inside one
                      consultation count ONCE (consultation-level distinct).
- "Diagnosed patient" A patient with at least one diagnosis case.
- "Patients seen"     A patient with at least one consultation of ANY status.
                      This is a clinic-utilization figure and is always
                      labelled as such — it is never mixed with diagnosed
                      counts.

POPULATION RULES
----------------
- Diagnosis figures only include COMPLETED consultations.
- Consultations without a usable diagnosis (null / empty / whitespace-only)
  are excluded everywhere; they never inflate "diagnosed" figures.
- Patients without a college (staff / other) are reported under an explicit
  "N/A" column instead of being silently dropped from per-college tables.

DATE SEMANTICS
--------------
All consultation-based reporting filters and buckets on
Consultation.created_at — the date the visit was recorded at the clinic.
Prescriptions, including later follow-up prescriptions, are attributed to
their consultation's date, so a report period always means "visits in the
period".

DISPLAY VS. DATA
----------------
Aggregation always uses the full diagnosis text as stored in the database.
Truncation happens only at presentation time via truncate_label(); the
underlying totals are never keyed on a shortened value.
"""

from collections import defaultdict

from django.db.models import Count

from consultations.models import Prescription

# Label for the "no college" bucket in per-college tables.
NA_LABEL = 'N/A'

# Default display width for diagnosis labels in HTML tables.
DIAGNOSIS_DISPLAY_LIMIT = 40

# Matches any diagnosis containing at least one non-whitespace character.
# Works on SQLite (Python re) and MySQL (ICU regex).
NONEMPTY_DIAGNOSIS_RE = r'\S'


def truncate_label(text, limit=DIAGNOSIS_DISPLAY_LIMIT):
    """Presentation-only shortening of a label. Data keeps the full text."""
    text = text or ''
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + '…'


def diagnosis_case_counts(completed_consultations, limit=None):
    """Aggregate diagnoses over completed consultations.

    Returns [{'diagnosis': <full text>, 'count': <distinct consultations>}, ...]
    ordered by count desc, then diagnosis asc (deterministic ranking by
    actual count — never by label or dict insertion order).
    """
    qs = (
        Prescription.objects
        .filter(consultation__in=completed_consultations)
        .filter(diagnosis__regex=NONEMPTY_DIAGNOSIS_RE)
        .values('diagnosis')
        .annotate(count=Count('consultation', distinct=True))
        .order_by('-count', 'diagnosis')
    )
    if limit is not None:
        qs = qs[:limit]
    return [{'diagnosis': row['diagnosis'], 'count': row['count']} for row in qs]


def diagnosis_college_matrix(completed_consultations, colleges):
    """College × diagnosis cross-tabulation keyed on full diagnosis text.

    Returns (column_names, rows):
      column_names  college abbreviations (ordered as `colleges`) + N/A
      rows          [{'diagnosis': <full text>, 'col_data': [...]}, ...]
                    ordered by row total desc, then diagnosis asc.

    Every diagnosis case appears in exactly one column, so each row's
    col_data sums to that diagnosis's case count — the matrix reconciles
    with diagnosis_case_counts() over the same queryset.
    """
    column_names = [c.abbreviation for c in colleges] + [NA_LABEL]
    na_index = len(colleges)
    # Aggregate on the stable college pk; abbreviations are display-only
    # (unique in the DB, but never used as the grouping key).
    college_index = {c.pk: i for i, c in enumerate(colleges)}

    grouped = (
        Prescription.objects
        .filter(consultation__in=completed_consultations)
        .filter(diagnosis__regex=NONEMPTY_DIAGNOSIS_RE)
        .values('diagnosis', 'consultation__patient__college_id')
        .annotate(count=Count('consultation', distinct=True))
    )

    # {full diagnosis: {column index: case count}} — full text keys only.
    buckets = defaultdict(lambda: defaultdict(int))
    for row in grouped:
        col = college_index.get(row['consultation__patient__college_id'], na_index)
        buckets[row['diagnosis']][col] += row['count']

    rows = [
        {
            'diagnosis': diagnosis,
            'col_data': [counts.get(i, 0) for i in range(len(column_names))],
        }
        for diagnosis, counts in buckets.items()
    ]
    rows.sort(key=lambda r: (-sum(r['col_data']), r['diagnosis']))
    return column_names, rows


def diagnosed_patients_by_college(consultations):
    """Distinct diagnosed patients per college over a consultation queryset.

    Used by the search-results breakdown (web + PDF). Patients without a
    college are reported under the explicit N/A label instead of an empty
    or None value.
    """
    rows = list(
        consultations
        .values('patient__college__abbreviation', 'patient__college__name')
        .annotate(count=Count('patient', distinct=True))
        .order_by('-count')
    )
    for row in rows:
        if not row['patient__college__abbreviation']:
            row['patient__college__abbreviation'] = NA_LABEL
            row['patient__college__name'] = 'No college'
    return rows


def patients_seen_by_college(consultations, colleges):
    """Distinct patients seen per college (clinic utilization, any status).

    Includes an N/A row for patients without a college so the column counts
    sum to the total number of distinct patients in the queryset.
    """
    grouped = (
        consultations
        .values('patient__college_id')
        .annotate(count=Count('patient', distinct=True))
    )
    counts = {row['patient__college_id']: row['count'] for row in grouped}

    rows = [
        {'patient__college__abbreviation': c.abbreviation, 'count': counts.get(c.pk, 0)}
        for c in colleges
    ]
    rows.append({'patient__college__abbreviation': NA_LABEL, 'count': counts.get(None, 0)})
    rows.sort(key=lambda r: (-r['count'], r['patient__college__abbreviation'] == NA_LABEL))
    return rows
