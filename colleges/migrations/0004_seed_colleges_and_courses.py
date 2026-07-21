"""
Data migration: seed default colleges and courses.

Colleges and courses use get_or_create so that admin edits/deletions are
preserved on subsequent migrate runs. Only records matching the default
data dict below are created if missing; manually added records are left
untouched, and manually deleted defaults are not re-created (because
they already exist in the DB — deletion is a conscious admin choice).
"""
from django.db import migrations

DEFAULT_COLLEGES = {
    'CAS': 'College of Arts and Sciences',
    'CBA': 'College of Business and Accountancy',
    'CCJE': 'College of Criminal Justice Education',
    'CTED': 'College of Teacher Education',
    'CAF': 'College of Agriculture and Forestry',
    'CIT': 'College of Industrial Technology',
}

DEFAULT_COURSES = {
    'CAS': [
        'Bachelor of Science in Information Technology',
        'Bachelor of Science in Computer Science',
    ],
    'CBA': [
        'Bachelor of Science in Human Resource Management',
        'Bachelor of Science in Office Administration',
        'Bachelor of Science in Business Administration',
    ],
    'CCJE': [
        'Bachelor of Science in Criminology',
    ],
    'CTED': [
        'Bachelor of Secondary Education Major in Science',
        'Bachelor of Secondary Education Major in Math',
        'Bachelor of Secondary Education Major in English',
        'Bachelor of Elementary Education',
    ],
    'CAF': [
        'Bachelor of Science in Agronomy',
        'Bachelor of Science in Forestry',
        'Bachelor of Science in Animal Science',
    ],
    'CIT': [
        'Bachelor of Science in Industrial Technology major in Computer Technology',
        'Bachelor of Science in Industrial Technology major in Automotive',
        'Bachelor of Science in Industrial Technology major in Electronics',
    ],
}


def seed_defaults(apps, schema_editor):
    College = apps.get_model('colleges', 'College')
    Course = apps.get_model('colleges', 'Course')

    for abbr, full_name in DEFAULT_COLLEGES.items():
        college, _ = College.objects.get_or_create(
            abbreviation=abbr,
            defaults={'name': full_name},
        )

    for abbr, course_names in DEFAULT_COURSES.items():
        try:
            college = College.objects.get(abbreviation=abbr)
        except College.DoesNotExist:
            continue
        for name in course_names:
            Course.objects.get_or_create(name=name, college=college)


def reverse_seed(apps, schema_editor):
    College = apps.get_model('colleges', 'College')
    Course = apps.get_model('colleges', 'Course')

    # Remove only the default courses that match our seed data
    for abbr, course_names in DEFAULT_COURSES.items():
        try:
            college = College.objects.get(abbreviation=abbr)
        except College.DoesNotExist:
            continue
        Course.objects.filter(name__in=course_names, college=college).delete()

    # Remove default colleges (only if they have no remaining courses)
    for abbr in DEFAULT_COLLEGES:
        try:
            college = College.objects.get(abbreviation=abbr)
        except College.DoesNotExist:
            continue
        if college.courses.count() == 0:
            college.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0003_seed_courses'),
    ]

    operations = [
        migrations.RunPython(seed_defaults, reverse_seed),
    ]
