from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# --- NOUVEAU MODÈLE ---
# 2. Table des départements
class Departement(models.Model):
    code = models.CharField(max_length=10, primary_key=True)  # ex: 'INFO'
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'departement'  # Correspond à votre SQL

    def __str__(self):
        return self.nom


# --- MODÈLE MODIFIÉ ---
# 1. Table utilisateur
class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        ETUDIANT = 'etudiant', 'Étudiant'
        ENSEIGNANT = 'enseignant', 'Enseignant'
        ADMIN = 'admin', 'Administrateur'

    # On remplace les champs nom/prenom de base
    first_name = None  # On n'utilise pas 'first_name'
    last_name = None  # On n'utilise pas 'last_name'

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    # mot_de_passe est géré par AbstractUser (champ 'password')
    # date_inscription est géré par AbstractUser (champ 'date_joined')

    role = models.CharField(max_length=20, choices=Role.choices)

    USERNAME_FIELD = 'email'  # On se connecte avec l'email
    REQUIRED_FIELDS = ['username', 'nom', 'prenom']  # 'username' est requis par défaut

    class Meta:
        db_table = 'utilisateur'  # Correspond à votre SQL

    def __str__(self):
        return self.email


# --- NOUVEAUX MODÈLES ---

# 3. Administrateur
class Administrateur(models.Model):
    # Clé primaire qui est aussi une clé étrangère vers Utilisateur
    id = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='administrateur'  # Pour l'accès inverse: user.administrateur
    )

    class Meta:
        db_table = 'administrateur'

    def __str__(self):
        return f"Admin: {self.id.nom} {self.id.prenom}"

# 4. Enseignant
class Enseignant(models.Model):
    id = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='enseignant'  # Pour l'accès inverse: user.enseignant
    )
    sexe = models.CharField(max_length=1, choices=[('H', 'Homme'), ('F', 'Femme')], blank=True, null=True)
    departement = models.ForeignKey(Departement, on_delete=models.RESTRICT, db_column='departement_code')

    class Meta:
        db_table = 'enseignant'

    def __str__(self):
        return f"Prof: {self.id.nom} {self.id.prenom}"


class Formation(models.Model):
    # On définit les choix possibles directement sur le modèle
    TYPE_CHOICES = [
        ('licence', 'Licence'),
        ('master', 'Master'),
    ]
    NIVEAU_CHOICES_LICENCE = [
        ('S1', 'S1'), ('S2', 'S2'), ('S3', 'S3'),
        ('S4', 'S4'), ('S5', 'S5'), ('S6', 'S6')
    ]
    NIVEAU_CHOICES_MASTER = [
        ('M1', 'M1'), ('M2', 'M2'), ('M3', 'M3'), ('M4', 'M4')
    ]
    # On combine les listes pour la validation dans la base de données
    NIVEAU_CHOICES = NIVEAU_CHOICES_LICENCE + NIVEAU_CHOICES_MASTER

    # Champs du modèle
    nom = models.CharField(max_length=150) # ex: "Génie Logiciel", "Droit des Affaires"
    type_formation = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='licence'
    )
    niveau = models.CharField(
        max_length=4,
        choices=NIVEAU_CHOICES,
        default='S1'
    )
    departement = models.ForeignKey(
        Departement,
        on_delete=models.CASCADE,
        related_name='formations'
    )

    def __str__(self):
        # Un nom plus clair, ex: "Licence S3 - Génie Logiciel (INFO)"
        return f"{self.get_type_formation_display()} {self.niveau} - {self.nom} ({self.departement.code})"

# 5. Étudiant
class Etudiant(models.Model):
    id = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='etudiant'
    )
    # Le niveau de l'étudiant est maintenant défini par sa formation
    formation = models.ForeignKey(
        Formation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'etudiant'

    def __str__(self):
        return f"Étu: {self.id.nom} {self.id.prenom}"