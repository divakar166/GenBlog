from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser

def index(request):
    return render(request, 'index.html')

@login_required
def generate(request):
    return render(request,'generator.html')

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            if CustomUser.objects.filter(email=email).exists():
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('index')
                else:
                    error_message = "Incorrect password."
                    return render(request, 'login.html', {'error_message': error_message})
            else:
                error_message = "User does not exist."
                return render(request, 'login.html', {'error_message': error_message})
        except Exception as e:
            print("Error:", e)
            error_message = "An error occurred during login."
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            if CustomUser.objects.filter(email=email).exists():
                error_message = "Email already exists."
                return render(request, 'register.html', {'error_message': error_message})
            new_user = CustomUser.objects.create_user(username=email, email=email, password=password, name=name)
            # login(request, new_user)
            return redirect('login')
        except Exception as e:
            print("Error:", e)
            error_message = "An error occurred during registration."
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')

def user_logout(request):
    logout(request)
    return redirect('index')