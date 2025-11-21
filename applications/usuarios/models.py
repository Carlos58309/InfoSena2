from django.db import models

class Usuario(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('administrador', 'Administrador'),
        ('aprendiz', 'Aprendiz'),
        ('instructor', 'Instructor'),
    ]

    tipo_documento_choices = [
        ('cedula de ciudadania', 'Cédula de Ciudadanía'),
        ('tarjeta de identidad', 'Tarjeta de Identidad'),
        ('cedula de extranjeria', 'Cédula de Extranjería'),
        ('PEP', 'PEP'),
        ('permiso por proteccion temporal', 'Permiso por Protección Temporal'),
    ]
    numero_documento = models.IntegerField(max_length=10, primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES)
    foto_perfil = models.ImageField(upload_to='usuarios/fotos/%Y/%m/%d/', blank=True, null=True)
    fecha_registro = models.DateField()
   
    tipo_documento = models.CharField(max_length=50, choices=tipo_documento_choices)
    numero_ficha = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"