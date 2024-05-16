from django.urls import path
from .views import *

urlpatterns = [
    path('',index , name='index'),
    path('generate',generate,name='generate'),
    path('login',user_login , name='login'),
    path('register',register , name='register'),
    path('logout', user_logout, name='logout'),
    path('gemini', gemini_view, name='gemini'),
    path('blog_submit', blog_submit, name='blog_submit')
]