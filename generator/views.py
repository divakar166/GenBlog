from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from .models import CustomUser, BlogPost, Like
import os
import google.generativeai as genai
from django.http import HttpResponse, JsonResponse
import json
from youtube_transcript_api import YouTubeTranscriptApi
import re

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

def topic_view(request):
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
    liked = False
    if request.user.is_authenticated:
        liked = Like.objects.filter(user=request.user, post=blog).exists()
    return render(request, 'blog_detail.html', {'blog': blog, 'liked': liked})

def user_blogs(request):
    blogs = BlogPost.objects.filter(author=request.user)
    return render(request, 'user_blogs.html', {'blogs':blogs})

def profile(request):
    return render(request, 'profile.html')

def like_blog_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(BlogPost, id=post_id)
        user = request.user
        if Like.objects.filter(user=user, post=post).exists():
            return JsonResponse({"error": "You have already liked this post"}, status=400)
        else:
            like = Like(user=user, post=post)
            like.save()
            post.likes += 1
            post.save()
            return JsonResponse({"likes": post.likes})
    return JsonResponse({"error": "Invalid request"}, status=400)

def get_youtube_video_id(url):
  pattern = r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=)?([^#&?]+)"
  match = re.search(pattern, url)
  if match:
    return match.group(1)
  else:
    return None


def yt_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        yt_link = data.get('yt_link', None)
        if yt_link:
            video_id = get_youtube_video_id(yt_link)
            if video_id:
                extraction = YouTubeTranscriptApi.get_transcript('vyQv563Y-fk')
                final_text = ""
                for item in extraction:
                    final_text += item['text']
                genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
                model = genai.GenerativeModel('gemini-pro')
                try:
                    response = model.generate_content(f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{final_text}")
                    text = response.text()
                    lines = text.splitlines()
                    if not lines:
                        first_line = 'Unknown'
                    else:
                        first_line = lines[0].strip()
                    user = CustomUser.objects.get(username=request.user)
                    blogPost = BlogPost.objects.create(
                        title=f"{first_line}",
                        content=response.text,
                        author=user
                    )
                    return HttpResponse(json.dumps({'content': response.text,'blogpost_id':blogPost.id}), content_type="application/json")
                except Exception as e:
                    print(e)
                    return HttpResponse(json.dumps({'error': str(e)}), status=500, content_type="application/json")
            else:
                return HttpResponse(json.dumps({'error': "Error in youtube link"}), status=400, content_type="application/json")
    else:
        return HttpResponse(json.dumps({'error': 'Method not allowed'}), status=400, content_type="application/json")