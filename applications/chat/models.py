from django.db import models

class Chat(models.Model):
    id_amistad = models.ForeignKey(
        'amistades.Amistad',   # Nombre de la app y modelo
        on_delete=models.CASCADE,
        related_name='chats'
    )

    class Meta:
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'

    def __str__(self):
        return f"Chat de la amistad #{self.id_amistad.id}"

