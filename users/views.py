from django.contrib.auth import login
from django.contrib.auth.forms import PasswordResetForm
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from tests.models import ResultadoValores, ResultadoDomino
from django.db.models import Count, Avg
from .forms import CustomUserChangeForm
from django.contrib.auth.views import LoginView

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                email_template_name='registration/password_reset_email.html',
                subject_template_name='registration/password_reset_subject.txt',
                from_email="no-reply@psymetrics.com",
                request=request
            )
            return redirect('password_reset_done')
    else:
        form = PasswordResetForm()
    return render(request, 'registration/password_reset.html', {'form': form})

@login_required
def dashboard(request):
    # Obtener estadísticas de pruebas
    resultados_valores = ResultadoValores.objects.filter(usuario=request.user)
    resultados_domino = ResultadoDomino.objects.filter(usuario=request.user)
    
    # Estadísticas generales
    total_valores = resultados_valores.count()
    total_domino = resultados_domino.count()
    total_tests = total_valores + total_domino
    
    # Últimas pruebas realizadas (combinando ambos tipos)
    ultimas_valores = list(resultados_valores.order_by('-fecha_completado')[:3])
    ultimas_domino = list(resultados_domino.order_by('-fecha')[:3])
    ultimas_pruebas = ultimas_valores + ultimas_domino
    
    # Ordenar por fecha correspondiente
    ultimas_pruebas = sorted(
        ultimas_pruebas,
        key=lambda x: x.fecha if hasattr(x, 'fecha') else x.fecha_completado,
        reverse=True
    )[:5]
    
    # Obtener promedio de puntuaciones
    avg_valores = resultados_valores.aggregate(
        teorico=Avg('teorico'),
        economico=Avg('economico'),
        estetico=Avg('estetico'),
        social=Avg('social'),
        politico=Avg('politico'),
        religioso=Avg('religioso')
    )
    
    context = {
        'user': request.user,
        'ultimas_pruebas': ultimas_pruebas,
        'total_tests': total_tests,
        'total_valores': total_valores,
        'total_domino': total_domino,
        'avg_valores': avg_valores,
    }
    return render(request, 'users/dashboard.html', context)
@login_required
def profile_view(request):
    user = request.user
    # Obtener historial completo de pruebas
    resultados_valores = ResultadoValores.objects.filter(usuario=user).order_by('-fecha_completado')
    resultados_domino = ResultadoDomino.objects.filter(usuario=user).order_by('-fecha')
    
    return render(request, 'users/profile.html', {
        'user': user,
        'resultados_valores': resultados_valores,
        'resultados_domino': resultados_domino
    })

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    return render(request, 'users/update_profile.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        # Redirigir a la URL solicitada originalmente o al dashboard
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return super().get_success_url()
