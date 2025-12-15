from django import forms
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.conf import settings
from api.models import Vendor
from .tokens import vendor_token_generator

class VendorPasswordResetForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = render_to_string(email_template_name, context)

        email_message = send_mail(
            subject, body, from_email, [to_email],
            html_message=render_to_string(html_email_template_name, context) if html_email_template_name else None,
        )
        return email_message

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=vendor_token_generator,
             from_email=None, request=None, html_email_template_name=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        email = self.cleaned_data["email"]
        try:
            vendor = Vendor.objects.get(email=email)
        except Vendor.DoesNotExist:
            # Don't reveal that the user doesn't exist
            return

        if not domain_override:
            current_site = request.get_host() if request else 'example.com'
            site_name = 'CoinVibe Pay'
        else:
            current_site = domain_override
            site_name = domain_override

        context = {
            'email': email,
            'domain': current_site,
            'site_name': site_name,
            'uid': urlsafe_base64_encode(force_bytes(vendor.pk)),
            'user': vendor,
            'token': token_generator.make_token(vendor),
            'protocol': 'https' if use_https else 'http',
        }
        
        self.send_mail(
            subject_template_name, email_template_name, context, from_email,
            email, html_email_template_name=html_email_template_name,
        )

class VendorSetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )
    
    def __init__(self, vendor, *args, **kwargs):
        self.vendor = vendor
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data["new_password"]
        self.vendor.password_hash = make_password(password)
        if commit:
            self.vendor.save()
        return self.vendor
