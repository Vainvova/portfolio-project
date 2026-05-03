from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.forms.models import BaseModelForm
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CustomUserCreationForm

class CustomLoginView(LoginView):
    template_name = "auth_system/login.html"
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = "auth_system:login"

class RegisterView(CreateView):
    template_name = "auth_system/register.html"
    form_class = CustomUserCreationForm
    
    def form_valid(self, form: BaseModelForm):
        user = form.save()
        login(self.request, user)
        return redirect(reverse_lazy("auth_system:login"))
