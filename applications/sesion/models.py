from django.db import models
from django.utils import timezone

class Sesion(models.Model):
    numero_documento = models.CharField(max_length=20)
    rol = models.CharField(
        max_length=50,
        choices=[
            ('Aprendiz', 'Aprendiz'),
            ('Instructor', 'Instructor'),
            ('Bienestar', 'Bienestar'),
        ]
    )
    fecha_inicio = models.DateTimeField(default=timezone.now)
    exito = models.BooleanField(default=False)  # True si inició sesión correctamente

    class Meta:
        db_table = 'sesion'
        verbose_name = 'Sesión'
        verbose_name_plural = 'Sesiones'

    def __str__(self):
        estado = "Exitosa" if self.exito else "Fallida"
        return f"{self.numero_documento} - {self.rol} ({estado})"
