# Generated by Django 5.0.14 on 2025-06-14 15:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_chatmessage_user_alter_chatmessage_session_id"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="chatmessage",
            name="user",
        ),
    ]
