from django.db import models
from ..usuarios.models import Usuario
from ..grupos.models import Grupo

class MiembroGrupo(models.Model):
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('aprendiz', 'Aprendiz'),
    ]

    id_admin = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario')
    id_grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, db_column='id_grupo')
    fecha_ingreso = models.DateField()
    rol = models.CharField(max_length=10, choices=ROL_CHOICES)

    class Meta:
        db_table = 'miembros_grupo'  # Usa el mismo nombre de la tabla SQL
        verbose_name = 'Miembro de Grupo'
        verbose_name_plural = 'Miembros de Grupo'

    def __str__(self):
        return f"{self.id_usuario.nombre} - {self.id_grupo.nombre_grupo} ({self.rol})"

