from django.db import models

class Ficha(models.Model):
    numero_ficha = models.IntegerField(primary_key=True)
    programa = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Ficha'
        verbose_name_plural = 'Fichas'

    def __str__(self):
        return f"Ficha {self.numero_ficha} - {self.programa}"

