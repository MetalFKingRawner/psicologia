from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Registro
    path('registro/', views.signup, name='signup'),
    #path('login/', auth_views.LoginView.as_view(
    #    template_name='login.html'), 
    #    name='login'
    #),
    # Redirección explícita usando el nombre de URL 'home'
    path(
        'logout/', 
        auth_views.LogoutView.as_view(next_page='home'), 
        name='logout'
    ),
    
    # Recuperación de contraseña
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ), name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), name='password_reset_complete'),
]