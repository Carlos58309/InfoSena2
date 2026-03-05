# applications/chat/urls.py
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Vistas principales
    path('', views.lista_chats, name='lista_chats'),
    path('room/<int:chat_id>/', views.chat_room, name='chat_room'),
    path('iniciar/<int:usuario_id>/', views.iniciar_chat, name='iniciar_chat'),
    path('enviar/<int:chat_id>/', views.enviar_mensaje, name='enviar_mensaje'),
    path('crear-grupo/', views.crear_grupo, name='crear_grupo'),

    # Funcionalidades extendidas (no-API)
    path('eliminar/<int:chat_id>/', views.eliminar_chat, name='eliminar_chat'),
    path('archivos/<int:chat_id>/', views.obtener_archivos_compartidos, name='archivos_compartidos'),

    # API endpoints — todos bajo api/
    path('api/mensajes/<int:chat_id>/',          views.api_obtener_mensajes,            name='api_obtener_mensajes'),
    path('api/enviar/<int:chat_id>/',             views.api_enviar_mensaje,              name='api_enviar_mensaje'),
    path('api/subir-archivo/<int:chat_id>/',      views.api_subir_archivo,               name='api_subir_archivo'),
    path('api/vaciar/<int:chat_id>/',             views.vaciar_mensajes,                 name='vaciar_mensajes'),
    path('api/silenciar/<int:chat_id>/',          views.silenciar_chat,                  name='silenciar_chat'),
    path('api/buscar/<int:chat_id>/',             views.buscar_mensajes,                 name='buscar_mensajes'),
    path('api/eliminar-mensajes/<int:chat_id>/',  views.eliminar_mensajes_seleccionados, name='eliminar_mensajes_seleccionados'),
    path('api/salir-grupo/<int:chat_id>/',    views.salir_grupo,    name='salir_grupo'),
    path('api/eliminar-grupo/<int:chat_id>/', views.eliminar_grupo, name='eliminar_grupo'),
    path('api/agregar-participantes/<int:chat_id>/', views.agregar_participantes, name='agregar_participantes'),
]