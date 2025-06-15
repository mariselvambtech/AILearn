from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# path('logout/',auth_views.LogoutView.as_view(next_page='login'),name='logout'),
urlpatterns = [
    path('', views.chat_page, name='chat_page'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/reset/', views.reset_chat, name='reset_chat'),
    path('login/',auth_views.LoginView.as_view(template_name='chat/login.html'),name='login'),
    path('logout/',views.custom_logout_view,name='logout'),
    path('register/', views.register, name='register'),
]