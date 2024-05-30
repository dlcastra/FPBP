from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from abc import ABC, abstractmethod


class RenderOrRedirect(ABC, TemplateView):
    trigger = "next"

    @property
    @abstractmethod
    def redirect_to(self):
        pass

    def get(self, request, *args, **kwargs):
        if self.trigger in request.GET:
            return redirect(self.redirect_to)

        return render(request, self.template_name)
