import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from comptes.models import Departement, Administrateur

class Command(BaseCommand):
    help = 'Seeds the database with initial security data and superuser.'

    def handle(self, *args, **options):
        self.stdout.write("Starting Security Seed...")

        User = get_user_model()
        
        # 1. Superuser
        admin_email = os.environ.get('SUPERUSER_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('SUPERUSER_PASSWORD', 'admin123')
        
        if not User.objects.filter(email=admin_email).exists():
            user = User.objects.create_superuser(
                email=admin_email,
                username=admin_email,
                password=admin_password,
                nom='Admin',
                prenom='System',
                role='admin'
            )
            # Create the OneToOne Administrateur profile
            Administrateur.objects.create(id=user)
            self.stdout.write(self.style.SUCCESS(f"Superuser {admin_email} created."))
        else:
            self.stdout.write(f"Superuser {admin_email} already exists.")

        # 2. Departments
        depts = [
            ('INFO', 'Informatique'),
            ('PH', 'Physique'),
            ('BIO', 'Biologie'),
        ]
        
        for code, nom in depts:
            obj, created = Departement.objects.get_or_create(code=code, defaults={'nom': nom})
            if created:
                 self.stdout.write(self.style.SUCCESS(f"Department {code} created."))

        self.stdout.write(self.style.SUCCESS("Security Seed Completed."))
