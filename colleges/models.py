from django.db import models


class College(models.Model):
    name = models.CharField(max_length=200, unique=True)
    abbreviation = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.abbreviation} — {self.name}'

    class Meta:
        verbose_name = 'College'
        verbose_name_plural = 'Colleges'
        ordering = ['name']


class Course(models.Model):
    name = models.CharField(max_length=200)
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name='courses',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} ({self.college.abbreviation})'

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['college__abbreviation', 'name']
        unique_together = [('name', 'college')]