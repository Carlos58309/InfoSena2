from django.db import models
from django.conf import settings

class Amistad(models.Model):
    PENDIENTE = 'pendiente'
    ACEPTADA = 'aceptada'
    RECHAZADA = 'rechazada'
    
    TIPOS_REACCION = [
        (PENDIENTE, 'Pendiente'),
        (ACEPTADA, 'Aceptada'),
        (RECHAZADA, 'Rechazada'),
    ]

    id_user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='amistades_user1')
    id_user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='amistades_user2')
    tipo_reaccion = models.CharField(
        max_length=9, choices=TIPOS_REACCION, default=PENDIENTE)

    class Meta:
        unique_together = ('id_user1', 'id_user2')  # Garantiza que la amistad sea única entre dos usuarios
        verbose_name = 'Amistad'
        verbose_name_plural = 'Amistades'

    def __str__(self):
        return f"Amistad entre {self.id_user1} y {self.id_user2}"

