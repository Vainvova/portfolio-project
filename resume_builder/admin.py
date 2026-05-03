from django.contrib import admin
from .models import ResumeTemplate, Resume, WorkExperience, Education, Skill, Announcement

@admin.register(ResumeTemplate)
class ResumeTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_premium', 'created_at']
    list_filter = ['is_premium', 'created_at']
    search_fields = ['name', 'description']

class WorkExperienceInline(admin.TabularInline):
    model = WorkExperience
    extra = 1

class EducationInline(admin.TabularInline):
    model = Education
    extra = 1

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'get_full_name', 'created_at', 'is_published']
    list_filter = ['is_published', 'created_at', 'template']
    search_fields = ['title', 'first_name', 'last_name', 'user__username']
    inlines = [WorkExperienceInline, EducationInline, SkillInline]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'

@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ['position', 'company', 'resume', 'start_date', 'current_job']
    list_filter = ['current_job', 'start_date']
    search_fields = ['position', 'company', 'resume__title']

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['degree', 'field_of_study', 'institution', 'resume', 'start_date']
    list_filter = ['start_date']
    search_fields = ['degree', 'field_of_study', 'institution']

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'resume']
    list_filter = ['level']
    search_fields = ['name']

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'
