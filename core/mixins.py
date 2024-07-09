from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import TemplateView, View, DetailView
from abc import ABC, abstractmethod

from core.helpers import post_request_details
from app.models import Comments


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


class RemoveCommentsMixin(ABC, View):
    def remove_comment(self, request, *args, **kwargs):
        """
        Remove comments from publication

        :param request: POST request
        :param args: Additional arguments.
        :param kwargs: Get answer_id (int) from URL path
        :return: HTTP or JSON response
            - If answer deleted with success: HTTP response status code is 204
            - If answer does not exist: JSON response {"error": "Comments does not exist"} and status code is 404
        """
        answer_id = self.kwargs.get("answer_id")
        try:
            answer = Comments.objects.get(id=answer_id)
            answer.delete()
            return HttpResponse(status=204)
        except Comments.DoesNotExist:
            return JsonResponse({"error": "Comments does not exist"}, status=404)


class DetailMixin(ABC, DetailView):
    @property
    @abstractmethod
    def get_model_class(self):
        pass

    @property
    @abstractmethod
    def get_form_class(self):
        pass

    @property
    @abstractmethod
    def render_main_template(self):
        pass

    @property
    @abstractmethod
    def render_edit_template(self):
        pass

    @property
    @abstractmethod
    def get_redirect_url(self):
        pass

    @abstractmethod
    def get_comments_template(self):
        pass

    def get_context_data(self, request, **kwargs):
        """
        :param request: GET and POST requests
        :param kwargs: get object 'pk' from URL
        :return: Dictionary context data for rendering object detail
            - user (str): Return username
            - model_class (list): Return model class by 'pk'
            - model_detail (dict): Return model data by 'pk'
            - comments (list): Returns comments that belong to the object, filtering them by 'pk' and 'content_type'
            - content_type (str): Determines which model this comments belongs
            - object_id (int): Return object id taken from URL as 'pk'
        """
        user = request.user
        pk = self.kwargs.get("pk")
        model_class = self.get_model_class().objects.filter(pk=pk).all()
        content_type = ContentType.objects.get_for_model(self.get_model_class())
        model_detail = get_object_or_404(self.get_model_class(), pk=pk)
        comments = Comments.objects.filter(object_id=pk, content_type=content_type).all()
        context = {
            "user": user,
            "model_class": model_class,
            "model_detail": model_detail,
            "comments": comments,
            "content_type": content_type,
            "object_id": pk,
        }

        return context

    def get_object(self, queryset=None):
        # Return object instance
        pk = self.kwargs.get("pk")
        return get_object_or_404(self.get_model_class(), pk=pk)

    def get(self, request, *args, **kwargs):
        """
        Displays the main template or template for the object being edited.
        Verifies that the user is authenticated and that the user is the author of the publication.

        :param request: HTTP request object that can include '?edit' parameter or None
        :param args: Additional arguments.
        :param kwargs: Taken object 'pk' from URL for 'model_detail'
        :return: Render template with context data
            - If request param is 'edit' and user is valid: Render edit template with dictionary context data
            - If request param is None: Render main template with object details
        """
        context = self.get_context_data(request, **kwargs)
        template = self.render_main_template()
        user_checker = request.user.is_authenticated and request.user.id == context["model_detail"].author_id

        # if "edit" in request.GET and user_checker:
        #     edit_template = self.render_edit_template()
        #     form_class = self.get_form_class()
        #     form = form_class(instance=self.get_object())
        #     return render(request, edit_template, {"form": form, **context})

        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        """
        Places the data into a function that checks the validity of the data then:
            - If the data is valid, the user is transferred to the given URL
            - For else cases must be displayed error message

        :param request: POST request with object data
        :param args: Additional arguments
        :param kwargs: Additional position arguments.
        :return: Redirect to the given URL or render template with context data:
            - If form is valid: Redirect to the given
            - If form is invalid: Return error message
        """
        form_class = self.get_form_class()
        form = form_class(request.POST, request.FILES, instance=self.get_object())
        redirect_response = post_request_details(request, form, self.get_redirect_url())

        if redirect_response:
            return redirect_response

        context = self.get_context_data(request, **kwargs)
        context["form"] = form
        return render(request, self.render_main_template(), context)


class ViewWitsContext(View):
    def get_context_data(self, request, **kwargs):
        context = {}
        return context


class BlackListMixin(ABC, ViewWitsContext):
    @property
    @abstractmethod
    def get_model_class(self):
        pass

    @property
    @abstractmethod
    def get_model_class_form(self):
        pass
