from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import TemplateView, View, DetailView
from abc import ABC, abstractmethod

from app.helpers import data_handler, post_request_details
from app.models import Comments
from users.models import CustomUser


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


class CommentsHandlerMixin(ABC, View):

    @abstractmethod
    def get_model_class(self):
        """
        Must be implemented to return the model class (Thread or Publications).
        """
        pass

    @abstractmethod
    def get_template(self):
        """
        Must be implemented to return the model class (Thread or Publications).
        """
        pass

    def get_context_data(self, request, **kwargs):
        pk = self.kwargs.get("pk")
        model_pk = self.kwargs.get("content_type_id")
        get_data = data_handler(request, pk, self.get_template(), model_pk)
        user_id = get_data["user_id"]
        model_class = self.get_model_class()
        instance = get_object_or_404(model_class, pk=pk)

        context = {"user_id": user_id, "instance": instance, "model_class": model_class, "pk": pk, "model_pk": model_pk}
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        instance = context["instance"]

        if instance:
            content = request.POST.get("feedback")
            try:
                user = CustomUser.objects.get(id=context["user_id"])
                content_type = ContentType.objects.get_for_model(instance.__class__)
                Comments.objects.create(
                    user=user,
                    title=instance.title,
                    context=content,
                    content_type=content_type,
                    object_id=context.get("pk"),
                )
                return JsonResponse(data_handler(request, context["pk"], self.get_template(), context["model_pk"]))
            except CustomUser.DoesNotExist:
                return JsonResponse({"message": "User not found"}, status=404)
            except Exception as e:
                return JsonResponse({"message": str(e)}, status=500)

        return JsonResponse({"message": "Invalid request"}, status=400)


class RemoveCommentsMixin(ABC, View):
    def remove_comment(self, request, *args, **kwargs):
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
        user = request.user
        pk = self.kwargs.get("pk")
        model_class = self.get_model_class().objects.filter(pk=pk).all()
        content_type = ContentType.objects.get_for_model(self.get_model_class())
        model_detail = get_object_or_404(self.get_model_class(), pk=pk)
        comments = Comments.objects.filter(object_id=pk, content_type=content_type).all()
        model_pk = self.get_model_class().objects.filter(pk=pk).all()[0].id
        get_context = data_handler(request, pk, self.get_comments_template(), model_pk)
        get_context["model_detail"] = model_detail
        context = {
            "user": user,
            "model_class": model_class,
            "model_detail": model_detail,
            "comments": comments,
            "get_context": get_context,
            "content_type": content_type,
        }

        return context

    def get_object(self, queryset=None):
        pk = self.kwargs.get("pk")
        return get_object_or_404(self.get_model_class(), pk=pk)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        template = self.render_main_template()
        user_checker = request.user.is_authenticated and request.user.id == context["model_detail"].author_id

        if "edit" in request.GET and user_checker:
            edit_template = self.render_edit_template()
            form_class = self.get_form_class()
            form = form_class(instance=self.get_object())
            return render(request, edit_template, {"form": form, **context})

        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(request.POST, request.FILES, instance=self.get_object())
        redirect_response = post_request_details(request, form, self.get_redirect_url())

        if redirect_response:
            return redirect_response

        context = self.get_context_data(request, **kwargs)
        context["form"] = form
        return render(request, self.render_main_template(), context)


class ViewWitsContext(View):
    def get_context_data(self, request):
        context = {}
        return context
