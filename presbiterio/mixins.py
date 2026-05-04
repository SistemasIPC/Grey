from django.contrib.auth.mixins import LoginRequiredMixin

class PresbiterioLoginRequiredMixin(LoginRequiredMixin):
    login_url = '/presbiterio/login/'