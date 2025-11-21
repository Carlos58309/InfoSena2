# chat/models.py
from django.db import models

class Mensaje(models.Model):
    LEIDO = 'leido'
    ENTREGADO = 'entregado'
    ENVIADO = 'enviado'

    ESTADOS = [
        (LEIDO, 'Leído'),
        (ENTREGADO, 'Entregado'),
        (ENVIADO, 'Enviado'),
    ]

    chat = models.OneToOneField(
        'chat.Chat',  # referencia al modelo Chat
        on_delete=models.CASCADE,
        primary_key=True,  # igual que en tu SQL
        related_name='mensaje'
    )
    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default=ENVIADO
    )

    class Meta:
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'

    def __str__(self):
        return f"Mensaje de chat #{self.chat.id} ({self.estado})"

