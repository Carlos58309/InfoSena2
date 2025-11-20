from django.urls import path
from . import views

app_name = 'registro'

urlpatterns = [
    path('', views.registro_view, name='registro'),
]