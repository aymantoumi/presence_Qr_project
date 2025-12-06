from django.db import models
from django.conf import settings
from comptes.models import Enseignant, Etudiant, Administrateur


# 6. Cours
class Cours(models.Model):
    SEMESTRE_CHOICES = [
        ('S1', 'S1'), ('S2', 'S2'), ('S3', 'S3'), ('S4', 'S4'),
        ('S5', 'S5'), ('S6', 'S6'), ('M1', 'M1'), ('M2', 'M2'),
        ('M3', 'M3'), ('M4', 'M4')
    ]

    nom = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    semestre_cible = models.CharField(max_length=3, choices=SEMESTRE_CHOICES)

    # Liens vers les nouvelles tables
    enseignant = models.ForeignKey(Enseignant, on_delete=models.RESTRICT, db_column='enseignant_id')
    cree_par = models.ForeignKey(Administrateur, on_delete=models.RESTRICT, db_column='cree_par')
    date_creation = models.DateTimeField(auto_now_add=True)

    # --- LIAISON MANQUANTE AJOUTÉE ---
    # C'est la liaison qui vous manquait
    etudiants = models.ManyToManyField(
        Etudiant,
        related_name='cours_inscrits',
        db_table='cours_etudiants'  # Table de liaison explicite
    )

    class Meta:
        db_table = 'cours'  # Correspond à votre SQL

    def __str__(self):
        return self.nom


# 7. Session de cours
class SessionCours(models.Model):
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, db_column='cours_id')
    enseignant = models.ForeignKey(Enseignant, on_delete=models.RESTRICT, db_column='enseignant_id')
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(blank=True, null=True)

    # --- MODIFIEZ CES DEUX LIGNES ---
    qr_token = models.CharField(max_length=512, unique=True, null=True, blank=True)
    qr_expiration = models.DateTimeField(null=True, blank=True)
    # --- FIN DE LA MODIFICATION ---

    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'session_cours'

    def __str__(self):
        return f"Session {self.cours.nom} du {self.date_debut.strftime('%d/%m')}"


# 8. Présence
class Presence(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, db_column='etudiant_id')
    session = models.ForeignKey(SessionCours, on_delete=models.CASCADE, db_column='session_id')
    horodatage_scan = models.DateTimeField(auto_now_add=True)
    qr_token_utilise = models.CharField(max_length=512)
    valide = models.BooleanField(default=True)

    class Meta:
        db_table = 'presence'
        unique_together = ('etudiant', 'session')  # 'unique_etudiant_session'