from allauth.socialaccount.models import SocialAccount, SocialApp
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .forms import CustomUserChangeForm


######## User Change Form ########
class CustomUserChangeView(LoginRequiredMixin, View):
    form_class = CustomUserChangeForm
    template_name = "account/change_user_data.html"
    success_url = "/change-data/"

    def get(self, request):
        form = self.form_class(instance=request.user)
        connections = SocialAccount.objects.filter(user_id=request.user.id)
        connected_provider_ids = connections.values_list('provider', flat=True)
        return render(
            request,
            self.template_name,
            {"form": form, "connections": connections, "connected_provider_ids": connected_provider_ids}
        )

    def post(self, request):
        form = self.form_class(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)
        else:
            connections = SocialAccount.objects.filter(user_id=request.user.id)
            connected_provider_ids = connections.values_list('provider', flat=True)
            return render(
                request,
                self.template_name,
                {"form": form, "connections": connections, "connected_provider_ids": connected_provider_ids}
            )


##################################


@login_required
def disconnect_account(request, provider):
    if request.method == 'POST':
        try:
            account = SocialAccount.objects.get(user=request.user, provider=provider)
            account.delete()
            return JsonResponse({'success': True})
        except SocialAccount.DoesNotExist:
            return JsonResponse({'error': 'Account not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)
