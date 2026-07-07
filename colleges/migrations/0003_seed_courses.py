# Data migration: seed courses per college
from django.db import migrations

COLLEGES_AND_COURSES = {
    'CAS': [
        'Bachelor of Science in Information Technology',
        'Bachelor of Science in Computer Science',
    ],
    'CBA': [
        'Bachelor of Science in Human Resource Management',
        'Bachelor of Science in Office Administration',
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


def seed_courses(apps, schema_editor):
    College = apps.get_model('colleges', 'College')
    Course = apps.get_model('colleges', 'Course')

    for abbreviation, course_names in COLLEGES_AND_COURSES.items():
        try:
            college = College.objects.get(abbreviation=abbreviation)
        except College.DoesNotExist:
            continue
        for name in course_names:
            Course.objects.get_or_create(name=name, college=college)


def reverse_seed_courses(apps, schema_editor):
    Course = apps.get_model('colleges', 'Course')
    Course.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0002_course'),
    ]

    operations = [
        migrations.RunPython(seed_courses, reverse_seed_courses),
    ]
