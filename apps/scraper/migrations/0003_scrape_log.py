from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScrapeLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error')], default='INFO', max_length=10)),
                ('message', models.TextField()),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='scraper.scraperjob')),
            ],
        ),
    ]
