from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_adminsettings_last_updated_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='blockchain_confirmations',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='transaction',
            name='chain_metadata',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='transaction',
            name='last_chain_check',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

