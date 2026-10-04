from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="jméno")),
                ("email", models.EmailField(max_length=254, verbose_name="e-mail")),
                ("message", models.TextField(max_length=4000, verbose_name="zpráva")),
                ("consent_given_at", models.DateTimeField(auto_now_add=True, verbose_name="souhlas se zpracováním")),
                ("email_sent", models.BooleanField(default=False, verbose_name="e-mail odeslán")),
                ("is_handled", models.BooleanField(default=False, verbose_name="vyřízeno")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="přijato")),
            ],
            options={
                "verbose_name": "zpráva z kontaktního formuláře",
                "verbose_name_plural": "zprávy z kontaktního formuláře",
                "ordering": ["-created_at"],
                "indexes": [models.Index(fields=["created_at"], name="contact_created_idx")],
            },
        ),
    ]
