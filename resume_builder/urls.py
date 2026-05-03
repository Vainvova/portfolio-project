from django.urls import path
from . import views

app_name = 'resume_builder'

urlpatterns = [
    path('', views.home, name='home'),
    path('templates/', views.template_gallery, name='template_gallery'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('resume/create/', views.create_resume, name='create_resume'),
    path('resume/<int:pk>/edit/', views.edit_resume, name='edit_resume'),
    path('resume/<int:pk>/delete/', views.delete_resume, name='delete_resume'),
    path('resume/<int:pk>/clone/', views.clone_resume, name='clone_resume'),
    path('resume/<int:pk>/preview/', views.preview_resume, name='preview_resume'),
]
