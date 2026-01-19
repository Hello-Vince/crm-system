# Generated migration to add missing fields for PermissionsMixin

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('companies', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        # Add is_staff field
        migrations.AddField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(default=False),
        ),
        # Add is_superuser field (from PermissionsMixin)
        migrations.AddField(
            model_name='user',
            name='is_superuser',
            field=models.BooleanField(
                default=False,
                help_text='Designates that this user has all permissions without explicitly assigning them.',
                verbose_name='superuser status',
            ),
        ),
        # Add groups field (from PermissionsMixin)
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(
                blank=True,
                help_text='The groups this user belongs to.',
                related_name='user_set',
                related_query_name='user',
                to='auth.group',
                verbose_name='groups',
            ),
        ),
        # Add user_permissions field (from PermissionsMixin)
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(
                blank=True,
                help_text='Specific permissions for this user.',
                related_name='user_set',
                related_query_name='user',
                to='auth.permission',
                verbose_name='user permissions',
            ),
        ),
        # Add updated_at field
        migrations.AddField(
            model_name='user',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        # Make company nullable
        migrations.AlterField(
            model_name='user',
            name='company',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='users',
                to='companies.company',
            ),
        ),
        # Update role choices
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('SYSTEM_ADMIN', 'System Admin'),
                    ('COMPANY_ADMIN', 'Company Admin'),
                    ('USER', 'User'),
                ],
                default='USER',
                max_length=20,
            ),
        ),
        # Update indexes
        migrations.RemoveIndex(
            model_name='user',
            name='users_user_company_9b5f6c_idx',
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='users_user_email_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['company'], name='users_user_company_idx'),
        ),
    ]
