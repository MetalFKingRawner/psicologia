from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='core_login'),  # Nombre único
    path('', views.index, name='home'),
    #path('', views.base_test, name='base_test'),  # Ruta para probar base.html
]