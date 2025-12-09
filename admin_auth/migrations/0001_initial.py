from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='AdminUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=64, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('full_name', models.CharField(blank=True, max_length=128)),
                ('role', models.CharField(choices=[('super_admin','super_admin'),('admin','admin'),('moderator','moderator'),('viewer','viewer')], default='viewer', max_length=32)),
                ('password_hash', models.CharField(max_length=256)),
                ('is_active', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=True)),
                ('failed_attempts', models.IntegerField(default=0)),
                ('locked_until', models.DateTimeField(blank=True, null=True)),
                ('session_token', models.CharField(blank=True, max_length=128, null=True)),
                ('session_expires_at', models.DateTimeField(blank=True, null=True)),
                ('password_reset_token', models.CharField(blank=True, max_length=128, null=True)),
                ('password_reset_expires_at', models.DateTimeField(blank=True, null=True)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('login_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='AdminSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_token', models.CharField(max_length=128)),
                ('expires_at', models.DateTimeField()),
                ('ip_address', models.CharField(blank=True, max_length=64)),
                ('user_agent', models.CharField(blank=True, max_length=256)),
                ('device_info', models.CharField(blank=True, max_length=256)),
                ('invalidated_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('admin_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='admin_auth.adminuser')),
            ],
        ),
        migrations.CreateModel(
            name='AdminAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=64)),
                ('action_description', models.CharField(blank=True, max_length=256)),
                ('ip_address', models.CharField(blank=True, max_length=64)),
                ('user_agent', models.CharField(blank=True, max_length=256)),
                ('session_token', models.CharField(blank=True, max_length=128)),
                ('risk_level', models.CharField(default='low', max_length=32)),
                ('suspicious', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('admin_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='admin_auth.adminuser')),
            ],
        ),
        migrations.CreateModel(
            name='AdminPasswordHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password_hash', models.CharField(max_length=256)),
                ('changed_by', models.CharField(blank=True, max_length=64)),
                ('reason', models.CharField(blank=True, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('admin_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='password_history', to='admin_auth.adminuser')),
            ],
        ),
    ]
