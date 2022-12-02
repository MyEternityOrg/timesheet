# Generated by Django 3.1 on 2021-02-02 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TimeSheet', '0003_auto_20210122_0943'),
    ]

    operations = [
        migrations.CreateModel(
            name='persons_audit',
            fields=[
                ('change_date', models.DateField(db_column='change_date', primary_key=True, serialize=False, unique=True)),
                ('count_state', models.FloatField(db_column='count_state')),
                ('count_staff', models.FloatField(db_column='count_staff')),
            ],
            options={
                'db_table': 'persons_audit',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='SettingTableTemp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count_day_last', models.IntegerField()),
                ('time_close_table', models.IntegerField()),
            ],
        ),
        migrations.AlterModelOptions(
            name='enterprises',
            options={'managed': False, 'ordering': ['enterprise_code']},
        ),
        migrations.AlterModelOptions(
            name='positions',
            options={'managed': False, 'ordering': ['full_name']},
        ),
    ]
