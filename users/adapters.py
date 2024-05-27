# from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
# from allauth.socialaccount.models import SocialAccount
# from django.contrib import messages
# from django.shortcuts import redirect
#
#
# class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
#     def pre_social_login(self, request, sociallogin):
#         user = sociallogin.user
#         provider = sociallogin.account.provider
#         max_connections = 1
#
#         if user.is_authenticated:
#
#             if not user.pk:
#                 user.save()
#
#             existing_accounts = SocialAccount.objects.filter(user=user, provider=provider)
#             if existing_accounts.count() >= max_connections:
#                 raise ValueError(f"You can only connect {max_connections} accounts from {provider}.")
#         else:
#             pass
