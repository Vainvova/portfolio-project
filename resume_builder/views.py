from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.forms import inlineformset_factory
from .models import Resume, ResumeTemplate, Announcement
from .forms import ResumeForm, WorkExperienceFormSet, EducationFormSet, SkillFormSet

def home(request):
    """Home page with hero section and features"""
    return render(request, 'resume_builder/home.html')

def template_gallery(request):
    """Template gallery page"""
    templates = ResumeTemplate.objects.all()
    return render(request, 'resume_builder/template_gallery.html', {'templates': templates})

@login_required
def dashboard(request):
    """Dashboard with user's resumes and announcements"""
    user_resumes = Resume.objects.filter(user=request.user).order_by('-updated_at')
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    context = {
        'resumes': user_resumes,
        'announcements': announcements,
    }
    return render(request, 'resume_builder/dashboard.html', context)

@login_required
def create_resume(request):
    """Create a new resume"""
    if request.method == 'POST':
        resume_form = ResumeForm(request.POST, request.FILES)
        
        if resume_form.is_valid():
            with transaction.atomic():
                resume = resume_form.save(commit=False)
                resume.user = request.user
                resume.save()
                
                # Handle formsets
                work_formset = WorkExperienceFormSet(request.POST, instance=resume)
                education_formset = EducationFormSet(request.POST, instance=resume)
                skill_formset = SkillFormSet(request.POST, instance=resume)
                
                if all([work_formset.is_valid(), education_formset.is_valid(), skill_formset.is_valid()]):
                    work_formset.save()
                    education_formset.save()
                    skill_formset.save()
                    
                    messages.success(request, 'Resume created successfully!')
                    return redirect('resume_builder:dashboard')
                else:
                    # If formsets are invalid, delete the resume and show errors
                    resume.delete()
                    messages.error(request, 'Please correct the errors below.')
        else:
            work_formset = WorkExperienceFormSet()
            education_formset = EducationFormSet()
            skill_formset = SkillFormSet()
    else:
        resume_form = ResumeForm()
        work_formset = WorkExperienceFormSet()
        education_formset = EducationFormSet()
        skill_formset = SkillFormSet()
    
    return render(request, 'resume_builder/resume_form.html', {
        'resume_form': resume_form,
        'work_formset': work_formset,
        'education_formset': education_formset,
        'skill_formset': skill_formset,
        'title': 'Create Resume'
    })

@login_required
def edit_resume(request, pk):
    """Edit an existing resume"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    if request.method == 'POST':
        resume_form = ResumeForm(request.POST, request.FILES, instance=resume)
        
        if resume_form.is_valid():
            with transaction.atomic():
                resume_form.save()
                
                work_formset = WorkExperienceFormSet(request.POST, instance=resume)
                education_formset = EducationFormSet(request.POST, instance=resume)
                skill_formset = SkillFormSet(request.POST, instance=resume)
                
                if all([work_formset.is_valid(), education_formset.is_valid(), skill_formset.is_valid()]):
                    work_formset.save()
                    education_formset.save()
                    skill_formset.save()
                    
                    messages.success(request, 'Resume updated successfully!')
                    return redirect('resume_builder:dashboard')
                else:
                    messages.error(request, 'Please correct the errors below.')
        else:
            work_formset = WorkExperienceFormSet(instance=resume)
            education_formset = EducationFormSet(instance=resume)
            skill_formset = SkillFormSet(instance=resume)
    else:
        resume_form = ResumeForm(instance=resume)
        work_formset = WorkExperienceFormSet(instance=resume)
        education_formset = EducationFormSet(instance=resume)
        skill_formset = SkillFormSet(instance=resume)
    
    return render(request, 'resume_builder/resume_form.html', {
        'resume_form': resume_form,
        'work_formset': work_formset,
        'education_formset': education_formset,
        'skill_formset': skill_formset,
        'title': 'Edit Resume'
    })

@login_required
@require_POST
def delete_resume(request, pk):
    """Delete a resume"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    resume.delete()
    messages.success(request, 'Resume deleted successfully!')
    return redirect('resume_builder:dashboard')

@login_required
def clone_resume(request, pk):
    """Clone an existing resume"""
    original_resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    with transaction.atomic():
        # Clone the main resume
        new_resume = Resume.objects.create(
            user=request.user,
            title=f"{original_resume.title} (Copy)",
            first_name=original_resume.first_name,
            last_name=original_resume.last_name,
            email=original_resume.email,
            phone=original_resume.phone,
            address=original_resume.address,
            photo=original_resume.photo,
            summary=original_resume.summary,
            template=original_resume.template,
        )
        
        # Clone related objects
        for work_exp in original_resume.work_experiences.all():
            WorkExperience.objects.create(
                resume=new_resume,
                company=work_exp.company,
                position=work_exp.position,
                start_date=work_exp.start_date,
                end_date=work_exp.end_date,
                current_job=work_exp.current_job,
                description=work_exp.description,
            )
        
        for education in original_resume.educations.all():
            Education.objects.create(
                resume=new_resume,
                institution=education.institution,
                degree=education.degree,
                field_of_study=education.field_of_study,
                start_date=education.start_date,
                end_date=education.end_date,
                current_study=education.current_study,
                gpa=education.gpa,
            )
        
        for skill in original_resume.skills.all():
            Skill.objects.create(
                resume=new_resume,
                name=skill.name,
                level=skill.level,
            )
    
    messages.success(request, 'Resume cloned successfully!')
    return redirect('resume_builder:dashboard')

@login_required
def preview_resume(request, pk):
    """Preview a resume"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    return render(request, 'resume_builder/resume_preview.html', {'resume': resume})
