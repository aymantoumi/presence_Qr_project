# presence/forms.py

from django import forms

from comptes.models import Departement, Formation
from .models import Cours, Enseignant, Etudiant


# --- Formulaire de Cours (déplacé ici) ---
class CoursForm(forms.ModelForm):
    # --- Champs de filtre (Non liés au modèle Cours directement) ---
    type_formation_filter = forms.ChoiceField(
        choices=[('', '--- Type ---')] + Formation.TYPE_CHOICES,
        required=False,
        label="1. Type de formation"
    )
    niveau_filter = forms.ChoiceField(
        choices=[('', '--- Niveau ---')], # Sera rempli par JS
        required=False,
        label="2. Niveau"
    )
    departement_filter = forms.ModelChoiceField(
        queryset=Departement.objects.all(),
        required=False,
        label="3. Département",
        empty_label="--- Département ---"
    )

    class Meta:
        model = Cours
        fields = ['nom', 'code', 'enseignant', 'etudiants'] # On garde les champs réels
        widgets = {
            # On cache la sélection manuelle complexe, le JS s'en chargera
            'etudiants': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}),
            'enseignant': forms.Select(attrs={'class': 'form-select'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On charge tous les étudiants mais on pourra les filtrer via JS
        self.fields['etudiants'].queryset = Etudiant.objects.select_related('id', 'formation').all()
        # Initialisation des niveaux si données existantes (optionnel)
        self.fields['niveau_filter'].choices = [('', '--- Choisir Type d\'abord ---')]


# --- Formulaire Département ---
class DepartementForm(forms.ModelForm):
    class Meta:
        model = Departement
        fields = ['code', 'nom']
        labels = {
            'code': 'Code Département (ex: INFO)',
            'nom': 'Nom complet (ex: Informatique)',
        }


# --- Formulaire Formation ---
class FormationForm(forms.ModelForm):
    class Meta:
        model = Formation
        # On ajoute les nouveaux champs
        fields = ['nom', 'type_formation', 'niveau', 'departement']
        labels = {
            'nom': 'Nom de la formation (ex: Génie Logiciel)',
            'type_formation': 'Type de formation',
            'niveau': 'Niveau',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # On commence avec une liste vide pour 'niveau'
        self.fields['niveau'].choices = [('', '---------')]

        # 1. Par défaut, on vide la liste (pour l'affichage initial propre)
        self.fields['niveau'].choices = [('', '---------')]

        # 2. CAS 1 : On reçoit des données POST (l'utilisateur a cliqué sur Enregistrer)
        if self.data:
            try:
                type_formation = self.data.get('type_formation')
                if type_formation == 'licence':
                    self.fields['niveau'].choices = Formation.NIVEAU_CHOICES_LICENCE
                elif type_formation == 'master':
                    self.fields['niveau'].choices = Formation.NIVEAU_CHOICES_MASTER
            except (ValueError, TypeError):
                pass  # En cas d'erreur, on laisse la liste vide ou par défaut

        # 3. CAS 2 : On modifie une formation existante (affichage de la valeur enregistrée)
        elif self.instance.pk and self.instance.type_formation:
            if self.instance.type_formation == 'licence':
                self.fields['niveau'].choices = Formation.NIVEAU_CHOICES_LICENCE
            elif self.instance.type_formation == 'master':
                self.fields['niveau'].choices = Formation.NIVEAU_CHOICES_MASTER

# --- Formulaires Enseignant ---
class EnseignantCreationForm(forms.Form):
    # Champs Utilisateur
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")

    # Champs Enseignant
    sexe = forms.ChoiceField(choices=[('H', 'Homme'), ('F', 'Femme')], required=False)
    departement = forms.ModelChoiceField(queryset=Departement.objects.all())


class EnseignantUpdateForm(forms.Form):
    # Champs Utilisateur
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100)
    email = forms.EmailField()

    # Champs Enseignant
    sexe = forms.ChoiceField(choices=[('H', 'Homme'), ('F', 'Femme')], required=False)
    departement = forms.ModelChoiceField(queryset=Departement.objects.all())


# --- Formulaires Étudiant ---
class EtudiantCreationForm(forms.Form):
    # Champs Utilisateur
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")

    type_formation = forms.ChoiceField(
        choices=[('', '----')] + Formation.TYPE_CHOICES,
        required=False,
        label="Filtrer par Type"
    )
    niveau = forms.ChoiceField(
        choices=[('', '----')],
        required=False,
        label="Filtrer par Niveau"
    )
    departement = forms.ModelChoiceField(
        queryset=Departement.objects.all(),
        required=False,
        label="Filtrer par Département"
    )

    formation = forms.ModelChoiceField(
        queryset=Formation.objects.all(),  # ✅ Toutes les formations chargées
        required=False,
        label="Formation (résultat du filtre)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cours = forms.ModelMultipleChoiceField(
        queryset=Cours.objects.all(),
        required=False,
        label="Inscrire aux Cours",
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '8'}),
        help_text="Sélectionnez les cours (Ctrl+Clic pour plusieurs)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.data:
            # 1. On valide le champ NIVEAU dynamiquement
            type_formation = self.data.get('type_formation')
            if type_formation == 'licence':
                self.fields['niveau'].choices = Formation.NIVEAU_CHOICES_LICENCE
            elif type_formation == 'master':
                self.fields['niveau'].choices = Formation.NIVEAU_CHOICES_MASTER

            # 2. On valide le champ FORMATION (votre code existant amélioré)
            try:
                formation_id = self.data.get('formation')
                if formation_id:
                    self.fields['formation'].queryset = Formation.objects.filter(pk=formation_id)
            except (ValueError, TypeError):
                pass


class EtudiantUpdateForm(forms.Form):
    # Champs Utilisateur
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100)
    email = forms.EmailField()

    # --- Champs de FILTRE ---
    type_formation = forms.ChoiceField(
        choices=[('', '----')] + Formation.TYPE_CHOICES,
        required=False,
        label="Filtrer par Type"
    )
    niveau = forms.ChoiceField(
        choices=[('', '----')],  # Par défaut vide
        required=False,
        label="Filtrer par Niveau"
    )
    departement = forms.ModelChoiceField(
        queryset=Departement.objects.all(),
        required=False,
        label="Filtrer par Département"
    )

    # --- VRAI Champ Étudiant ---
    formation = forms.ModelChoiceField(
        queryset=Formation.objects.all(),
        required=False,
        label="Formation"
    )

    # --- AJOUT DU CHAMP COURS (Pour être cohérent avec la création) ---
    cours = forms.ModelMultipleChoiceField(
        queryset=Cours.objects.all(),
        required=False,
        label="Inscrire aux Cours",
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '8'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # On doit déterminer quel type de formation est utilisé (pour charger les bons niveaux)
        current_type = None

        # 1. Si on reçoit des données POST (l'utilisateur clique sur Enregistrer)
        if self.data:
            current_type = self.data.get('type_formation')

            # Validation dynamique de la formation choisie
            try:
                formation_id = self.data.get('formation')
                if formation_id:
                    self.fields['formation'].queryset = Formation.objects.filter(pk=formation_id)
            except (ValueError, TypeError):
                pass

        # 2. Sinon, si on a des données initiales (affichage du formulaire)
        elif 'initial' in kwargs:
            current_type = kwargs['initial'].get('type_formation')

        # --- Mise à jour des choix de NIVEAU ---
        if current_type == 'licence':
            self.fields['niveau'].choices = Formation.NIVEAU_CHOICES_LICENCE
        elif current_type == 'master':
            self.fields['niveau'].choices = Formation.NIVEAU_CHOICES_MASTER