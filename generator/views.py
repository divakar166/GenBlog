from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from .models import CustomUser, BlogPost
import os
import google.generativeai as genai
from django.http import HttpResponse
import json 

def index(request):
    if request.user.is_authenticated:
        blogs = BlogPost.objects.filter(is_published=True).exclude(author=request.user).order_by('-created_at')[:3]
    else:
        blogs = BlogPost.objects.filter(is_published=True).order_by('-created_at')[:3]
    return render(request, 'index.html', context={'blogs': blogs})

def explore(request):
    if request.user.is_authenticated:
        blogs = BlogPost.objects.filter(is_published=True).exclude(author=request.user).order_by('-created_at')
    else:
        blogs = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'explore.html', context={'blogs': blogs})

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

def gemini_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        topic = data.get('topic', None)
        if topic:
            genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            model = genai.GenerativeModel('gemini-pro')
            try:
                response = model.generate_content(f"Write an attractive blog on the topic: {topic}.")
                user = CustomUser.objects.get(username=request.user)
                blogPost = BlogPost.objects.create(
                    title=f"{topic}",
                    content=response.text,
                    author=user
                )
                return HttpResponse(json.dumps({'content': response.text,'blogpost_id':blogPost.id}), content_type="application/json")
            except Exception as e:
                print(e)
                return HttpResponse(json.dumps({'error': str(e)}), status=500, content_type="application/json")  # Return error message with status code 500
        else:
            return HttpResponse(json.dumps({'error': 'Topic is missing'}), status=400, content_type="application/json")  # Return error message with status code 400
    else:
        return HttpResponse(json.dumps({'error': 'Method not allowed'}), status=405, content_type="application/json")

def blog_submit(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        blogID = data.get('blogID')
        action = data.get('action')
        visibility = int(data.get('visibility'))
        if action == 'submit':
            try:
                blog = BlogPost.objects.get(id=blogID)
                blog.is_published = True
                blog.is_public = bool(visibility)
                blog.save()
                return HttpResponse(json.dumps({'content':"success"}), content_type="application/json")
            except Exception as e:
                print(e)
                return HttpResponse(json.dumps({'error': e}), content_type="application/json")
        elif action == 'cancel':
            try:
                blog = BlogPost.objects.get(id=blogID)
                blog.delete()
                return HttpResponse(json.dumps({'content':"success"}), content_type="application/json")
            except Exception as e:
                print(e)
                return HttpResponse(json.dumps({'error': e}), content_type="application/json")
        return HttpResponse(json.dumps({'error': 'Method not allowed'}), content_type="application/json")
        
def blog_detail(request, slug):
    blog = get_object_or_404(BlogPost, slug=slug)
    return render(request, 'blog_detail.html', {'blog': blog})