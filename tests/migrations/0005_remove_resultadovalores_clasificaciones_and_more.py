# Generated by Django 5.0.3 on 2025-06-02 21:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0004_alter_resultadovalores_clasificaciones_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resultadovalores',
            name='clasificaciones',
        ),
        migrations.RemoveField(
            model_name='resultadovalores',
            name='descripcion_dominante',
        ),
        migrations.RemoveField(
            model_name='resultadovalores',
            name='fecha_creacion',
        ),
        migrations.RemoveField(
            model_name='resultadovalores',
            name='meta_dominante',
        ),
        migrations.RemoveField(
            model_name='resultadovalores',
            name='rangos_valores',
        ),
        migrations.RemoveField(
            model_name='resultadovalores',
            name='valor_dominante',
        ),
    ]
