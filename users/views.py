from django.urls import reverse_lazy
from django.views.generic import CreateView

from users.forms import CreationForm


class SignUp(CreateView):
    """Класс для отображения формы регистрациию."""
    form_class = CreationForm
    success_url = reverse_lazy("login")
    template_name = "signup.html"



