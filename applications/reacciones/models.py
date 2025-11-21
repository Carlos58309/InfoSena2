from django.db import models

class Reaccion(models.Model):
    TIPO_REACCION_CHOICES = [
        ('me gusta', 'Me gusta'),
        ('me encanta', 'Me encanta'),
        ('me enoja', 'Me enoja'),
        ('me divierte', 'Me divierte'),
        ('me asusta', 'Me asusta'),
    ]

    id_reaccion = models.AutoField(primary_key=True)
    id_publicacion = models.ForeignKey(
        'publicaciones.Publicacion',  # 👈 referencia al modelo Publicacion
        on_delete=models.CASCADE,
        db_column='id_publicacion'
    )
    id_usuario = models.ForeignKey(
        'usuarios.Usuario',  # 👈 referencia al modelo Usuario
        on_delete=models.CASCADE,
        db_column='id_usuario'
    )
    tipo_reaccion = models.CharField(max_length=20, choices=TIPO_REACCION_CHOICES)

    class Meta:
        db_table = 'reacciones'  # mantiene el mismo nombre que la tabla SQL

    def __str__(self):
        return f"{self.id_usuario} → {self.tipo_reaccion} en publicación {self.id_publicacion}"
