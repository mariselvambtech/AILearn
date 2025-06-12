from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('ask/', views.ask_view, name='ask'),
    path('toggle_cot/', views.toggle_cot, name='toggle_cot'),
]
