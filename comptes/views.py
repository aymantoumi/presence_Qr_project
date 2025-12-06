# comptes/views.py

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def dashboard_redirect_view(request):
    """
    Redirige l'utilisateur vers le bon tableau de bord
    en fonction de son rôle.
    """
    if request.user.role == 'admin':
        # CORRECTION : On redirige vers la NOUVELLE liste de cours
        return redirect('cours_list')
    elif request.user.role == 'enseignant':
        return redirect('dashboard_enseignant')
    elif request.user.role == 'etudiant':
        return redirect('scanner')
    else:
        return redirect('home')

# (Nous ajouterons les vues CRUD pour Etudiant/Enseignant ici plus tard)