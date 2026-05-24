from django import forms
from django.forms.models import BaseInlineFormSet

from .models import Education, Resume, Skill, WorkExperience


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['title', 'first_name', 'last_name', 'email', 'phone', 'address', 'photo', 'summary']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class OptionalInlineFormMixin:
    """New (empty) inline rows are optional in the browser; validate on the server if partially filled."""

    required_if_any = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            for field in self.fields.values():
                field.required = False

    def _row_has_data(self, cleaned_data):
        for name in self.required_if_any:
            value = cleaned_data.get(name)
            if value not in (None, '', False):
                return True
        return False

    def clean(self):
        cleaned_data = super().clean()
        if not self._row_has_data(cleaned_data):
            return cleaned_data
        for name in self.required_if_any:
            if not cleaned_data.get(name):
                self.add_error(name, "Це поле обовʼязкове.")
        return cleaned_data


class WorkExperienceForm(OptionalInlineFormMixin, forms.ModelForm):
    required_if_any = ('company', 'position', 'start_date', 'description')

    class Meta:
        model = WorkExperience
        fields = ['company', 'position', 'start_date', 'end_date', 'current_job', 'description']
        widgets = {
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'current_job': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EducationForm(OptionalInlineFormMixin, forms.ModelForm):
    required_if_any = ('institution', 'degree', 'field_of_study', 'start_date')

    class Meta:
        model = Education
        fields = ['institution', 'degree', 'field_of_study', 'start_date', 'end_date', 'current_study', 'gpa']
        widgets = {
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'degree': forms.TextInput(attrs={'class': 'form-control'}),
            'field_of_study': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'current_study': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'gpa': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SkillForm(OptionalInlineFormMixin, forms.ModelForm):
    required_if_any = ('name', 'level')

    class Meta:
        model = Skill
        fields = ['name', 'level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }


class BaseOptionalInlineFormSet(BaseInlineFormSet):
    def _should_delete_form(self, form):
        if super()._should_delete_form(form):
            return True
        if not form.instance.pk and not form.has_changed():
            return True
        return False


WorkExperienceFormSet = forms.inlineformset_factory(
    Resume,
    WorkExperience,
    form=WorkExperienceForm,
    formset=BaseOptionalInlineFormSet,
    extra=1,
    can_delete=True,
)

EducationFormSet = forms.inlineformset_factory(
    Resume,
    Education,
    form=EducationForm,
    formset=BaseOptionalInlineFormSet,
    extra=1,
    can_delete=True,
)

SkillFormSet = forms.inlineformset_factory(
    Resume,
    Skill,
    form=SkillForm,
    formset=BaseOptionalInlineFormSet,
    extra=1,
    can_delete=True,
)
