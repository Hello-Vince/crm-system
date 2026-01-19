"""
Management command to seed initial data for easy testing.
Creates a superuser and sample companies.
"""

from django.core.management.base import BaseCommand
from companies.models import Company
from users.models import User


class Command(BaseCommand):
    help = "Seed database with initial data for testing"

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding database...\n")

        # Create superuser (SYSTEM_ADMIN - no company needed)
        if not User.objects.filter(email="admin@crm.com").exists():
            superuser = User.objects.create_user(
                email="admin@crm.com",
                password="admin123",
                first_name="System",
                last_name="Admin",
                role=User.UserRole.SYSTEM_ADMIN,
                is_staff=True,
                is_superuser=True,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Created superuser: {superuser.email} (password: admin123)"
                )
            )
        else:
            self.stdout.write("⏭️  Superuser already exists\n")

        # Create sample companies
        company_a, created = Company.objects.get_or_create(
            name="Acme Corporation", defaults={"parent": None}
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Created company: {company_a.name}")
            )
        else:
            self.stdout.write(f"⏭️  Company already exists: {company_a.name}\n")

        company_b, created = Company.objects.get_or_create(
            name="Acme West Division", defaults={"parent": company_a}
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Created company: {company_b.name} (child of {company_a.name})"
                )
            )
        else:
            self.stdout.write(f"⏭️  Company already exists: {company_b.name}\n")

        company_c, created = Company.objects.get_or_create(
            name="Acme East Division", defaults={"parent": company_a}
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Created company: {company_c.name} (child of {company_a.name})"
                )
            )
        else:
            self.stdout.write(f"⏭️  Company already exists: {company_c.name}\n")

        # Create sample users for each company
        if not User.objects.filter(email="admin.acme@crm.com").exists():
            user_acme = User.objects.create_user(
                email="admin.acme@crm.com",
                password="acme123",
                first_name="John",
                last_name="Manager",
                company=company_a,
                role=User.UserRole.COMPANY_ADMIN,
                is_staff=True,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Created company admin: {user_acme.email} (password: acme123)"
                )
            )
        else:
            self.stdout.write("⏭️  Company admin already exists\n")

        if not User.objects.filter(email="user.west@crm.com").exists():
            user_west = User.objects.create_user(
                email="user.west@crm.com",
                password="west123",
                first_name="Jane",
                last_name="Smith",
                company=company_b,
                role=User.UserRole.USER,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Created user: {user_west.email} (password: west123)"
                )
            )
        else:
            self.stdout.write("⏭️  User already exists\n")

        # Create an independent company (NOT part of Acme hierarchy)
        # This showcases multi-tenant isolation
        company_global, created = Company.objects.get_or_create(
            name="GlobalTech Industries", defaults={"parent": None}
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Created company: {company_global.name} (independent)"
                )
            )
        else:
            self.stdout.write(f"⏭️  Company already exists: {company_global.name}\n")

        # Create admin for the independent company
        if not User.objects.filter(email="admin.global@crm.com").exists():
            user_global = User.objects.create_user(
                email="admin.global@crm.com",
                password="global123",
                first_name="Sarah",
                last_name="Chen",
                company=company_global,
                role=User.UserRole.COMPANY_ADMIN,
                is_staff=True,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Created company admin: {user_global.email} (password: global123)"
                )
            )
        else:
            self.stdout.write("⏭️  GlobalTech admin already exists\n")

        self.stdout.write(
            "\n" + self.style.SUCCESS("🎉 Database seeded successfully!\n")
        )
        self.stdout.write("📋 Test Credentials:\n")
        self.stdout.write("   - System Admin: admin@crm.com / admin123\n")
        self.stdout.write("   - Acme Admin: admin.acme@crm.com / acme123\n")
        self.stdout.write("   - GlobalTech Admin: admin.global@crm.com / global123\n")
        self.stdout.write("   - Regular User: user.west@crm.com / west123\n")
