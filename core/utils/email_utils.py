from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_html_email(subject, to_email, template_name, context):
    """Generic HTML email sender"""
    html_content = render_to_string(template_name, context)
    text_content = f"{subject}\n\n" + "\n".join([f"{k}: {v}" for k, v in context.items()])
    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


def send_login_credentials(email, username, password):
    context = {"username": username, "password": password}
    send_html_email("Your MEDSRAVTS Account Details", email, "emails/welcome_email.html", context)


def send_email_changed_notification(username, old_email, new_email):
    context = {"username": username, "old_email": old_email, "new_email": new_email}
    send_html_email("MEDSRAVTS Email Changed", old_email, "emails/email_changed.html", context)
    send_html_email("MEDSRAVTS Email Changed", new_email, "emails/email_changed.html", context)
