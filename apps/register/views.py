from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect


def register_view(request):
    errors = []
    username = ""
    email = ""

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username:
            errors.append("Enter a username.")
        elif User.objects.filter(username=username).exists():
            errors.append("Username already exists.")

        if not email:
            errors.append("Enter an email address.")

        if not password:
            errors.append("Enter a password.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")

        # Django's validators need a user object when the username is similar.
        if password and not errors:
            try:
                validate_password(password, user=User(username=username, email=email))
            except ValidationError as error:
                errors.extend(error.messages)

        if not errors:
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            return redirect("login:login")

    return render(request, "register/register.html", {
        "errors": errors,
        "username": username,
        "email": email,
    })
