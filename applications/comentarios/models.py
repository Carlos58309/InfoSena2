from django.db import models


class Comentario(models.Model):
    id_comentario = models.AutoField(primary_key=True)
    id_publicacion = models.ForeignKey(
        'publicaciones.Publicacion',  # 👈 nombre_app.NombreModelo
        on_delete=models.CASCADE,
        db_column='id_publicacion'
    )
    id_usuario = models.ForeignKey(
        'usuarios.Usuario',  # 👈 nombre_app.NombreModelo
        on_delete=models.CASCADE,
        db_column='id_usuario'
    )
    comentarios = models.CharField(max_length=1000)
    fecha_comentario = models.DateField()

    class Meta:
        db_table = 'comentarios'
