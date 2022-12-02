# Generated by Django 3.1 on 2021-01-22 06:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('TimeSheet', '0002_auto_20210121_1820'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profileuser',
            name='id',
        ),
        migrations.AlterField(
            model_name='profileuser',
            name='entreprise',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='TimeSheet.enterprises'),
        ),
        migrations.AlterField(
            model_name='profileuser',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterModelTable(
            name='timesheetplane',
            table='shift_data_p',
        ),
    ]