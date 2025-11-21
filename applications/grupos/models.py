from django.db import models

class Grupo(models.Model):
    TIPO_REACCION_CHOICES = [
        ('abierto', 'Abierto'),
        ('cerrado', 'Cerrado'),
        ('privado', 'Privado'),
    ]

    id_grupo = models.AutoField(primary_key=True)
    id_admin = models.IntegerField()
    nombre_grupo = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=100)
    tipo_reaccion = models.CharField(max_length=10, choices=TIPO_REACCION_CHOICES)
    fecha_creacion = models.DateField()

    class Meta:
        db_table = 'grupos'  # 👈 indica a Django que use la tabla existente
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'

    def __str__(self):
        return self.nombre_grupo
