from django.contrib import admin
from .models import College, Course


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('abbreviation', 'name', 'created_at')
    search_fields = ('name', 'abbreviation')
    ordering = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'college')
    list_filter = ('college',)
    search_fields = ('name',)