
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth import authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import CitizenRegistrationForm


def register_view(request):

    if request.user.is_authenticated:
        return redirect('role_redirect')

    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                'Your CivicConnect account has been created!'
            )

            return redirect('role_redirect')

    else:
        form = CitizenRegistrationForm()

    return render(
        request,
        'accounts/register.html',
        {'form': form}
    )


def login_view(request):

    if request.user.is_authenticated:
        return redirect('role_redirect')

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('role_redirect')

        messages.error(
            request,
            'Invalid username or password.'
        )

    return render(request, 'accounts/login.html')


@login_required
def role_redirect(request):

    user = request.user

    if user.is_superuser or user.role == 'admin':
        return redirect('admin_dashboard')

    elif user.role == 'manager':
        return redirect('manager_dashboard')

    elif user.role == 'citizen':
        return redirect('citizen_dashboard')

    logout(request)
    messages.error(request, 'Your account has an invalid role.')
    return redirect('login')


@login_required
def logout_view(request):

    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('login')

    return redirect('role_redirect')
