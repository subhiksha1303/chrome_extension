from django.urls import path
from .views import home, analyze_news  # Import views

urlpatterns = [
    path("", home, name="home"),  # Home Page
    path("analyze_news/", analyze_news, name="analyze_news"),  # API Endpoint
]
