from django.conf import settings
from django.db import migrations, models


def publish_existing_resumes(apps, schema_editor):
    Resume = apps.get_model('resume_builder', 'Resume')
    Resume.objects.filter(is_published=False).update(is_published=True)


def seed_announcements(apps, schema_editor):
    Announcement = apps.get_model('resume_builder', 'Announcement')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    if Announcement.objects.exists():
        return

    author = User.objects.filter(is_staff=True).first() or User.objects.first()
    if not author:
        return

    items = [
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
    Announcement.objects.bulk_create([
        Announcement(title=item['title'], content=item['content'], author=author, is_active=True)
        for item in items
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('resume_builder', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='resumetemplate',
            name='category',
            field=models.CharField(
                choices=[
                    ('professional', 'Професійні'),
                    ('creative', 'Креативні'),
                    ('modern', 'Сучасні'),
                    ('simple', 'Прості'),
                ],
                default='professional',
                max_length=20,
            ),
        ),
        migrations.RunPython(publish_existing_resumes, migrations.RunPython.noop),
        migrations.RunPython(seed_announcements, migrations.RunPython.noop),
    ]
