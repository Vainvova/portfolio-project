import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import EducationFormSet, ResumeForm, SkillFormSet, WorkExperienceFormSet
from .models import Announcement, Education, Resume, ResumeTemplate, Skill, WorkExperience

DRAFT_PHOTO_SESSION_KEY = 'resume_draft_photo'
User = get_user_model()

SORT_OPTIONS = {
    'updated': '-updated_at',
    'title': 'title',
    'created': '-created_at',
}

DEFAULT_ANNOUNCEMENTS = [
    {
        'title': 'Ласкаво просимо до Будівника резюме',
        'content': (
            'Створюйте професійні резюме за кілька хвилин. '
            'Використовуйте шаблони, додавайте досвід роботи та експортуйте результат.'
        ),
    },
    {
        'title': 'Нові шаблони макетів',
        'content': (
            'У галереї шаблонів зʼявилися професійні, креативні та мінімалістичні макети. '
            'Оберіть стиль, який підходить вашій сфері.'
        ),
    },
    {
        'title': 'Порада тижня',
        'content': (
            'Підлаштовуйте резюме під кожну вакансію: змінюйте опис досвіду '
            'та виділяйте релевантні навички.'
        ),
    },
]


def _bind_formsets(post_data, resume_instance):
    return (
        WorkExperienceFormSet(post_data, instance=resume_instance),
        EducationFormSet(post_data, instance=resume_instance),
        SkillFormSet(post_data, instance=resume_instance),
    )


def _store_draft_photo(request):
    photo = request.FILES.get('photo')
    if not photo:
        return None
    path = default_storage.save(
        f'draft_photos/{request.user.id}_{uuid.uuid4().hex}_{photo.name}',
        photo,
    )
    old_path = request.session.get(DRAFT_PHOTO_SESSION_KEY)
    if old_path and default_storage.exists(old_path):
        default_storage.delete(old_path)
    request.session[DRAFT_PHOTO_SESSION_KEY] = path
    return default_storage.url(path)


def _clear_draft_photo(request):
    path = request.session.pop(DRAFT_PHOTO_SESSION_KEY, None)
    if path and default_storage.exists(path):
        default_storage.delete(path)


def _get_draft_photo_url(request):
    path = request.session.get(DRAFT_PHOTO_SESSION_KEY)
    if path and default_storage.exists(path):
        return default_storage.url(path)
    return None


def _get_photo_preview_url(request, resume_form):
    if request.FILES.get('photo'):
        return _store_draft_photo(request)
    if getattr(resume_form.instance, 'photo', None):
        try:
            return resume_form.instance.photo.url
        except (ValueError, AttributeError):
            pass
    return _get_draft_photo_url(request)


def _ensure_default_announcements():
    if Announcement.objects.filter(is_active=True).exists():
        return
    author = User.objects.filter(is_staff=True).first() or User.objects.first()
    if not author:
        return
    Announcement.objects.bulk_create([
        Announcement(title=item['title'], content=item['content'], author=author)
        for item in DEFAULT_ANNOUNCEMENTS
    ])


def _apply_draft_photo_to_resume(request, resume):
    if resume.photo:
        _clear_draft_photo(request)
        return
    path = request.session.get(DRAFT_PHOTO_SESSION_KEY)
    if path and default_storage.exists(path):
        with default_storage.open(path) as draft_file:
            resume.photo.save(path.rsplit('/', 1)[-1], draft_file, save=False)
    _clear_draft_photo(request)


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
    _ensure_default_announcements()

    sort_key = request.GET.get('sort', 'updated')
    order_by = SORT_OPTIONS.get(sort_key, '-updated_at')
    user_resumes = Resume.objects.filter(user=request.user).order_by(order_by)
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]

    published_count = user_resumes.filter(is_published=True).count()
    draft_count = user_resumes.filter(is_published=False).count()

    context = {
        'resumes': user_resumes,
        'announcements': announcements,
        'sort': sort_key,
        'published_count': published_count,
        'draft_count': draft_count,
    }
    return render(request, 'resume_builder/dashboard.html', context)


@login_required
def create_resume(request):
    """Create a new resume"""
    photo_preview_url = None

    if request.method == 'POST':
        resume_form = ResumeForm(request.POST, request.FILES)
        resume_instance = Resume(user=request.user)
        work_formset, education_formset, skill_formset = _bind_formsets(
            request.POST, resume_instance
        )

        formsets_valid = all([
            work_formset.is_valid(),
            education_formset.is_valid(),
            skill_formset.is_valid(),
        ])

        if resume_form.is_valid() and formsets_valid:
            with transaction.atomic():
                resume = resume_form.save(commit=False)
                resume.user = request.user
                resume.is_published = True
                _apply_draft_photo_to_resume(request, resume)
                resume.save()

                work_formset.instance = resume
                education_formset.instance = resume
                skill_formset.instance = resume
                work_formset.save()
                education_formset.save()
                skill_formset.save()

            messages.success(request, 'Resume created successfully!')
            return redirect('resume_builder:dashboard')

        photo_preview_url = _get_photo_preview_url(request, resume_form)
        messages.error(request, 'Please correct the errors below.')
    else:
        _clear_draft_photo(request)
        resume_form = ResumeForm()
        work_formset = WorkExperienceFormSet()
        education_formset = EducationFormSet()
        skill_formset = SkillFormSet()

    return render(request, 'resume_builder/resume_form.html', {
        'resume_form': resume_form,
        'work_formset': work_formset,
        'education_formset': education_formset,
        'skill_formset': skill_formset,
        'photo_preview_url': photo_preview_url,
        'title': 'Create Resume',
    })


@login_required
def edit_resume(request, pk):
    """Edit an existing resume"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    photo_preview_url = None

    if request.method == 'POST':
        resume_form = ResumeForm(request.POST, request.FILES, instance=resume)
        work_formset, education_formset, skill_formset = _bind_formsets(
            request.POST, resume
        )

        formsets_valid = all([
            work_formset.is_valid(),
            education_formset.is_valid(),
            skill_formset.is_valid(),
        ])

        if resume_form.is_valid() and formsets_valid:
            with transaction.atomic():
                resume = resume_form.save(commit=False)
                resume.is_published = True
                resume.save()
                work_formset.save()
                education_formset.save()
                skill_formset.save()

            messages.success(request, 'Resume updated successfully!')
            return redirect('resume_builder:dashboard')

        photo_preview_url = _get_photo_preview_url(request, resume_form)
        messages.error(request, 'Please correct the errors below.')
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
        'photo_preview_url': photo_preview_url,
        'title': 'Edit Resume',
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
            is_published=False,
        )

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
