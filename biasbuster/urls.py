from django.urls import path
from .views import analyze_news  # This imports from the biasbuster app

urlpatterns = [
    path('analyze_news/', analyze_news, name='analyze_news'),
]
