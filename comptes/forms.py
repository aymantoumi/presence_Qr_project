from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import Utilisateur, Etudiant, Enseignant, Departement, Formation


class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ('email', 'nom', 'prenom', 'role')
    # Champs de base de l'utilisateur
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)
    nom = forms.CharField(required=True)
    prenom = forms.CharField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[
        (Utilisateur.Role.ETUDIANT, 'Étudiant'),
        (Utilisateur.Role.ENSEIGNANT, 'Enseignant'),
    ])

    # Champs spécifiques
    semestre = None
    departement = forms.ModelChoiceField(queryset=Departement.objects.all(), required=False)
    formation = forms.ModelChoiceField(queryset=Formation.objects.all(), required=False)


    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == Utilisateur.Role.ETUDIANT and not cleaned_data.get('formation'):
            raise forms.ValidationError("La formation est requise pour un étudiant.")
        if role == Utilisateur.Role.ENSEIGNANT and not cleaned_data.get('departement'):
            raise forms.ValidationError("Le département est requis pour un enseignant.")
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = self.cleaned_data['role']
        user.save()

        if user.role == Utilisateur.Role.ETUDIANT:
            Etudiant.objects.create(
                id=user,
                formation=self.cleaned_data['formation']
            )
        elif user.role == Utilisateur.Role.ENSEIGNANT:
            Enseignant.objects.create(
                id=user,
                departement=self.cleaned_data['departement']
            )
        return user


# --- NOUVEAUX FORMULAIRES POUR LE CRUD ADMIN ---

class EnseignantAdminForm(forms.ModelForm):
    # Champs pour le modèle Utilisateur
    email = forms.EmailField(label="Email (Identifiant)")
    nom = forms.CharField(label="Nom")
    prenom = forms.CharField(label="Prénom")

    class Meta:
        model = Enseignant
        fields = ['email', 'nom', 'prenom', 'sexe', 'departement']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Remplir les champs Utilisateur si on modifie
            self.fields['email'].initial = self.instance.id.email
            self.fields['nom'].initial = self.instance.id.nom
            self.fields['prenom'].initial = self.instance.id.prenom


class EtudiantAdminForm(forms.ModelForm):
    # Champs pour le modèle Utilisateur
    email = forms.EmailField(label="Email (Identifiant)")
    nom = forms.CharField(label="Nom")
    prenom = forms.CharField(label="Prénom")

    class Meta:
        model = Etudiant
        fields = ['email', 'nom', 'prenom', 'formation']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['email'].initial = self.instance.id.email
            self.fields['nom'].initial = self.instance.id.nom
            self.fields['prenom'].initial = self.instance.id.prenom

