# applications/chat/views.py
"""Views de chat con moderación, archivos adjuntos y eliminación por usuario."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Max, Prefetch
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from applications.moderacion.decorators import moderar_mensaje_chat
from applications.usuarios.models import Usuario
from applications.amistades.models import Amistad
from applications.moderacion.moderacion_service import ModeracionService
from .models import Chat, Mensaje, MensajeEliminadoParaUsuario, ChatVaciadoPorUsuario
import logging
import json
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

moderador = ModeracionService()

TIPOS_PERMITIDOS = {
    "image/jpeg":        ("imagen",    ".jpg"),
    "image/png":         ("imagen",    ".png"),
    "image/gif":         ("imagen",    ".gif"),
    "image/webp":        ("imagen",    ".webp"),
    "video/mp4":         ("video",     ".mp4"),
    "video/webm":        ("video",     ".webm"),
    "video/ogg":         ("video",     ".ogg"),
    "video/quicktime":   ("video",     ".mov"),
    "application/pdf":                                                          ("documento", ".pdf"),
    "application/msword":                                                       ("documento", ".doc"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document":  ("documento", ".docx"),
    "application/vnd.ms-excel":                                                 ("documento", ".xls"),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":        ("documento", ".xlsx"),
    "application/vnd.ms-powerpoint":                                            ("documento", ".ppt"),
    "application/vnd.openxmlformats-officedocument.presentationml.presentation":("documento", ".pptx"),
    "text/plain":                                                               ("documento", ".txt"),
}

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

_CATEGORIAS_GRAVES = [
    "sexual", "sexual/minors", "violence/graphic",
    "hate/threatening", "self-harm/intent",
]

LIMITE_ELIMINAR_PARA_TODOS_HORAS = 24


def obtener_usuario_actual(request):
    from applications.registro.models import Aprendiz, Instructor, Bienestar

    usuario_id = request.session.get("usuario_id")
    tipo_perfil = request.session.get("tipo_usuario")

    if not usuario_id or not tipo_perfil:
        return None

    try:
        if tipo_perfil == "aprendiz":
            datos_usuario = Aprendiz.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == "instructor":
            datos_usuario = Instructor.objects.get(numero_documento=usuario_id)
        elif tipo_perfil == "bienestar":
            datos_usuario = Bienestar.objects.get(numero_documento=usuario_id)
        else:
            return None
    except Exception:
        return None

    try:
        return Usuario.objects.get(documento=datos_usuario.numero_documento)
    except Usuario.DoesNotExist:
        return None
    except Usuario.MultipleObjectsReturned:
        return Usuario.objects.filter(documento=datos_usuario.numero_documento).first()


# ══════════════════════════════════════════════════════════════
#  VISTAS PRINCIPALES
# ══════════════════════════════════════════════════════════════


def lista_chats(request):
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect("sesion:home")

    todos_los_chats = Chat.objects.filter(
        participantes=usuario_actual
    ).annotate(
        ultimo_mensaje_fecha=Max("mensajes__enviado")
    ).order_by("-ultimo_mensaje_fecha")

    chats_enriquecidos = []
    for c in todos_los_chats:
        ultimo_msg = c.ultimo_mensaje_para_usuario(usuario_actual)
        chats_enriquecidos.append({
            "chat": c,
            "nombre": c.obtener_nombre_para_usuario(usuario_actual),
            "foto": c.obtener_foto_para_usuario(usuario_actual),
            "ultimo_mensaje": ultimo_msg,
            "mensajes_no_leidos": c.mensajes_no_leidos_para_usuario(usuario_actual),
            "activo": False,
            "es_grupo": c.is_group,
        })

    context = {
        "usuario": usuario_actual,
        "chats": chats_enriquecidos,
        "amigos": Amistad.obtener_amigos(usuario_actual),
        "chat": None,
        "mensajes": [],
        "chat_nombre": None,
        "chat_foto": None,
        "is_group": False,
        "otro_usuario": None,
    }
    return render(request, "chat.html", context)



def chat_room(request, chat_id):
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect("sesion:home")

    chat = get_object_or_404(Chat, id=chat_id, participantes=usuario_actual)

    # Solo mensajes visibles para este usuario
    mensajes = chat.mensajes_visibles_para_usuario(usuario_actual)

    for mensaje in mensajes.filter(visto=False).exclude(autor=usuario_actual):
        mensaje.marcar_como_visto()

    todos_los_chats = Chat.objects.filter(
        participantes=usuario_actual
    ).annotate(
        ultimo_mensaje_fecha=Max("mensajes__enviado")
    ).order_by("-ultimo_mensaje_fecha")

    chats_enriquecidos = []
    for c in todos_los_chats:
        chats_enriquecidos.append({
            "chat": c,
            "nombre": c.obtener_nombre_para_usuario(usuario_actual),
            "foto": c.obtener_foto_para_usuario(usuario_actual),
            "ultimo_mensaje": c.ultimo_mensaje_para_usuario(usuario_actual),
            "mensajes_no_leidos": c.mensajes_no_leidos_para_usuario(usuario_actual),
            "activo": c.id == chat.id,
            "es_grupo": c.is_group,
        })

    # Obtener el otro usuario en chat individual (para panel de info)
    otro_usuario = None
    if not chat.is_group:
        otro_usuario = chat.participantes.exclude(id=usuario_actual.id).first()

    # Estado de silenciado para mostrar el botón correctamente
    silenciado = False
    if otro_usuario:
        try:
            from applications.notificaciones.models import ChatSilenciado
            silenciado = ChatSilenciado.esta_silenciado(usuario=usuario_actual, emisor=otro_usuario)
        except Exception:
            pass
    es_participante_activo = chat.participantes.filter(id=usuario_actual.id).exists()
    es_admin_grupo = chat.is_group and chat.admin_grupo == usuario_actual
    context = {
        "usuario": usuario_actual,
        "chat": chat,
        "mensajes": mensajes,
        "chats": chats_enriquecidos,
        "chat_nombre": chat.obtener_nombre_para_usuario(usuario_actual),
        "chat_foto": chat.obtener_foto_para_usuario(usuario_actual),
        "is_group": chat.is_group,
        "otro_usuario": otro_usuario,
        "silenciado": silenciado,
        "es_participante_activo": es_participante_activo,
        "es_admin_grupo": es_admin_grupo,
        "amigos": Amistad.obtener_amigos(usuario_actual),
    }
    return render(request, "chat.html", context)



def iniciar_chat(request, usuario_id):
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect("sesion:home")

    otro_usuario = get_object_or_404(Usuario, id=usuario_id)
    if not Amistad.son_amigos(usuario_actual, otro_usuario):
        messages.error(request, "Solo puedes chatear con tus amigos.")
        return redirect("sesion:amigos")

    chat = Chat.obtener_o_crear_chat_individual(usuario_actual, otro_usuario)
    return redirect("chat:chat_room", chat_id=chat.id)



@moderar_mensaje_chat
def enviar_mensaje(request, chat_id):
    if request.method != "POST":
        return redirect("chat:chat_room", chat_id=chat_id)

    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect("sesion:home")

    chat = get_object_or_404(Chat, id=chat_id, participantes=usuario_actual)
    contenido = request.POST.get("contenido", "").strip()

    if contenido:
        resultado = moderador.moderar_texto(contenido)
        if resultado.get("bloqueado"):
            cats = resultado.get("categorias_detectadas", [])
            if resultado.get("metodo") == "filtro_local":
                messages.warning(request, "Por favor, evita usar lenguaje ofensivo.")
            elif any(c in _CATEGORIAS_GRAVES for c in cats):
                messages.error(request, "Tu mensaje fue bloqueado por contenido inapropiado.")
                return redirect("chat:chat_room", chat_id=chat_id)
            else:
                messages.warning(request, "Por favor, mantén un lenguaje respetuoso.")

        try:
            Mensaje.objects.create(chat=chat, autor=usuario_actual, contenido=contenido)
            chat.actualizado_en = timezone.now()
            chat.save(update_fields=["actualizado_en"])
        except ValidationError as e:
            messages.error(request, str(e))

    return redirect("chat:chat_room", chat_id=chat_id)


def crear_grupo(request):
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        messages.error(request, "No se pudo identificar tu usuario.")
        return redirect("sesion:home")

    if request.method == "POST":
        nombre_grupo      = request.POST.get("nombre_grupo", "").strip()
        descripcion       = request.POST.get("descripcion", "").strip()
        participantes_ids = request.POST.getlist("participantes")
        foto_grupo        = request.FILES.get("foto_grupo")   # ← NUEVO

        if not nombre_grupo:
            messages.error(request, "El nombre del grupo es obligatorio.")
            return redirect("chat:crear_grupo")
        if not participantes_ids:
            messages.error(request, "Debes seleccionar al menos un participante.")
            return redirect("chat:crear_grupo")

        if moderador.moderar_texto(nombre_grupo).get("bloqueado"):
            messages.error(request, "El nombre del grupo contiene contenido inapropiado.")
            return redirect("chat:crear_grupo")

        if descripcion and moderador.moderar_texto(descripcion).get("bloqueado"):
            messages.error(request, "La descripción contiene contenido inapropiado.")
            return redirect("chat:crear_grupo")

        # Crear el grupo
        grupo = Chat.crear_grupo(
            nombre=nombre_grupo,
            admin=usuario_actual,
            participantes_ids=participantes_ids,
            descripcion=descripcion,
        )

        # ── Guardar foto si se subió ──────────────────────────────────────────
        if foto_grupo:
            grupo.foto_grupo = foto_grupo
            grupo.save(update_fields=["foto_grupo"])
        # ─────────────────────────────────────────────────────────────────────

        messages.success(request, f"Grupo '{nombre_grupo}' creado exitosamente.")
        return redirect("chat:chat_room", chat_id=grupo.id)

    context = {
        "usuario": usuario_actual,
        "amigos": Amistad.obtener_amigos(usuario_actual),
    }
    return render(request, "crear_grupo.html", context)


# ══════════════════════════════════════════════════════════════
#  API AJAX — MENSAJES
# ══════════════════════════════════════════════════════════════

def api_obtener_mensajes(request, chat_id):
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    chat = get_object_or_404(Chat, id=chat_id, participantes=usuario_actual)
    ultimo_id = request.GET.get("ultimo_id", 0)

    # Respetar mensajes eliminados/vaciados para este usuario
    mensajes_nuevos = chat.mensajes_visibles_para_usuario(usuario_actual).filter(id__gt=ultimo_id)

    for m in mensajes_nuevos:
        if m.autor != usuario_actual and not m.visto:
            m.marcar_como_visto()

    data = [{
        "id": m.id,
        "autor_id": m.autor.id,
        "autor_nombre": m.autor.nombre,
        "contenido": m.contenido,
        "enviado": m.enviado.isoformat(),
        "tiempo_transcurrido": m.tiempo_transcurrido(),
        "es_mio": m.autor.id == usuario_actual.id,
        "puede_eliminar_para_todos": m.puede_eliminar_para_todos(usuario_actual),
    } for m in mensajes_nuevos]

    return JsonResponse({"mensajes": data, "total": len(data)})


def api_enviar_mensaje(request, chat_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    chat = get_object_or_404(Chat, id=chat_id, participantes=usuario_actual)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    contenido = data.get("contenido", "").strip()
    if not contenido:
        return JsonResponse({"error": "El mensaje no puede estar vacío"}, status=400)

    resultado = moderador.moderar_texto(contenido)
    if resultado.get("bloqueado"):
        cats = resultado.get("categorias_detectadas", [])
        if any(c in _CATEGORIAS_GRAVES for c in cats):
            return JsonResponse({
                "success": False,
                "error": "Mensaje bloqueado por contenido inapropiado.",
                "razon": resultado.get("razon"),
            }, status=400)

    try:
        mensaje = Mensaje.objects.create(chat=chat, autor=usuario_actual, contenido=contenido)
        chat.actualizado_en = timezone.now()
        chat.save(update_fields=["actualizado_en"])
        return JsonResponse({
            "success": True,
            "mensaje": {
                "id": mensaje.id,
                "autor_id": mensaje.autor.id,
                "autor_nombre": mensaje.autor.nombre,
                "contenido": mensaje.contenido,
                "enviado": mensaje.enviado.isoformat(),
                "tiempo_transcurrido": mensaje.tiempo_transcurrido(),
                "puede_eliminar_para_todos": mensaje.puede_eliminar_para_todos(usuario_actual),
            },
        })
    except ValidationError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@require_POST
def api_subir_archivo(request, chat_id):
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    chat = get_object_or_404(Chat, id=chat_id, participantes=usuario_actual)
    archivo = request.FILES.get("archivo")
    if not archivo:
        return JsonResponse({"error": "No se recibió ningún archivo"}, status=400)

    mime = archivo.content_type
    if mime not in TIPOS_PERMITIDOS:
        return JsonResponse({"error": f"Tipo de archivo no permitido: {mime}."}, status=400)
    if archivo.size > MAX_FILE_SIZE:
        return JsonResponse({"error": "Archivo demasiado grande. Máximo: 25 MB."}, status=400)

    tipo_archivo, ext = TIPOS_PERMITIDOS[mime]
    nombre_unico = f"chat_{chat_id}/{uuid.uuid4().hex}{ext}"
    ruta_guardada = default_storage.save(f"chat_archivos/{nombre_unico}", ContentFile(archivo.read()))
    url_archivo = default_storage.url(ruta_guardada)

    caption = request.POST.get("caption", "").strip()
    contenido_msg = caption if caption else archivo.name

    try:
        mensaje = Mensaje.objects.create(
            chat=chat, autor=usuario_actual, contenido=contenido_msg,
            archivo=ruta_guardada, tipo_archivo=tipo_archivo,
            nombre_archivo=archivo.name, tamanio_archivo=archivo.size,
        )
    except Exception as e:
        logger.warning(f"Fallback sin campos extendidos: {e}")
        mensaje = Mensaje.objects.create(chat=chat, autor=usuario_actual, contenido=contenido_msg)

    chat.actualizado_en = timezone.now()
    chat.save(update_fields=["actualizado_en"])

    return JsonResponse({
        "success": True,
        "mensaje": {
            "id": mensaje.id,
            "autor_id": mensaje.autor.id,
            "autor_nombre": mensaje.autor.nombre,
            "contenido": contenido_msg,
            "tipo_archivo": tipo_archivo,
            "url_archivo": url_archivo,
            "nombre_archivo": archivo.name,
            "tamanio": archivo.size,
            "enviado": mensaje.enviado.isoformat(),
        },
    })


# ══════════════════════════════════════════════════════════════
#  API AJAX — BÚSQUEDA DE MENSAJES
# ══════════════════════════════════════════════════════════════

def buscar_mensajes(request, chat_id):
    """
    Busca mensajes en el chat.
    - Respeta mensajes eliminados/vaciados para el usuario.
    - Devuelve fecha formateada y offset (posición en el chat) para scroll.
    - Busca por contenido exacto e insensible a mayúsculas/tildes aproximado.
    """
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"error": "Query vacío"}, status=400)

    try:
        chat = Chat.objects.get(id=chat_id, participantes=usuario_actual)

        # Buscar solo en mensajes visibles para este usuario
        mensajes_visibles = chat.mensajes_visibles_para_usuario(usuario_actual)

        resultados_qs = mensajes_visibles.filter(
            contenido__icontains=query
        ).select_related("autor").order_by("enviado")[:50]

        # Calcular el índice de cada mensaje en el chat para el scroll
        todos_ids = list(mensajes_visibles.values_list("id", flat=True))

        resultados = []
        for m in resultados_qs:
            try:
                posicion = todos_ids.index(m.id)
            except ValueError:
                posicion = -1

            resultados.append({
                "id": m.id,
                "contenido": m.contenido,
                "autor": m.autor.nombre,
                "es_mio": m.autor.id == usuario_actual.id,
                "enviado": m.enviado.strftime("%d/%m/%Y %H:%M"),
                "tiempo_transcurrido": m.tiempo_transcurrido(),
                "posicion": posicion,  # índice en el listado visible → para scroll exacto
            })

        return JsonResponse({"success": True, "resultados": resultados, "total": len(resultados)})

    except Chat.DoesNotExist:
        return JsonResponse({"error": "Chat no encontrado"}, status=404)


# ══════════════════════════════════════════════════════════════
#  API AJAX — ELIMINAR / VACIAR
# ══════════════════════════════════════════════════════════════

@require_POST
def vaciar_mensajes(request, chat_id):
    """
    Vacía el chat solo para el usuario actual.
    Los otros participantes siguen viendo todos los mensajes.
    Los mensajes NO se borran de la BD.
    """
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    try:
        chat = Chat.objects.get(id=chat_id, participantes=usuario_actual)
        chat.vaciar_para_usuario(usuario_actual)
        logger.info(f"Chat {chat_id} vaciado para {usuario_actual.nombre} (otros usuarios no afectados)")
        return JsonResponse({"success": True, "message": "Chat vaciado para ti"})
    except Chat.DoesNotExist:
        return JsonResponse({"error": "Chat no encontrado"}, status=404)


@require_POST
def eliminar_mensajes_seleccionados(request, chat_id):
    """
    Elimina mensajes seleccionados con dos modos:
    - 'solo_para_mi': marca como eliminado para el usuario actual (todos los mensajes seleccionados)
    - 'para_todos': elimina de la BD, pero solo si:
        1. El mensaje fue enviado por el usuario actual
        2. Fue enviado hace menos de LIMITE_ELIMINAR_PARA_TODOS_HORAS horas

    Body JSON:
    {
        "mensaje_ids": [1, 2, 3],
        "para_todos": false
    }
    """
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    mensaje_ids = data.get("mensaje_ids", [])
    para_todos = data.get("para_todos", False)

    if not mensaje_ids:
        return JsonResponse({"error": "No se especificaron mensajes"}, status=400)

    try:
        chat = Chat.objects.get(id=chat_id, participantes=usuario_actual)
    except Chat.DoesNotExist:
        return JsonResponse({"error": "Chat no encontrado"}, status=404)

    # Solo mensajes que pertenecen a este chat
    mensajes = Mensaje.objects.filter(id__in=mensaje_ids, chat=chat)

    eliminados_para_mi = 0
    eliminados_para_todos = 0
    no_permitidos = 0

    if para_todos:
        # Intentar eliminar para todos — solo los propios y dentro del límite
        for m in mensajes:
            if m.puede_eliminar_para_todos(usuario_actual):
                m.delete()
                eliminados_para_todos += 1
            else:
                # Si no puede eliminarlo para todos, lo elimina solo para él
                MensajeEliminadoParaUsuario.objects.get_or_create(
                    mensaje=m, usuario=usuario_actual
                )
                eliminados_para_mi += 1
                no_permitidos += 1
    else:
        # Solo para mí
        for m in mensajes:
            MensajeEliminadoParaUsuario.objects.get_or_create(
                mensaje=m, usuario=usuario_actual
            )
            eliminados_para_mi += 1

    resultado = {
        "success": True,
        "eliminados_para_todos": eliminados_para_todos,
        "eliminados_para_mi": eliminados_para_mi,
    }

    if para_todos and no_permitidos > 0:
        resultado["advertencia"] = (
            f"{no_permitidos} mensaje(s) solo se eliminaron para ti "
            f"porque son de otro usuario o tienen más de {LIMITE_ELIMINAR_PARA_TODOS_HORAS}h."
        )

    return JsonResponse(resultado)


@require_POST
def eliminar_chat(request, chat_id):
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    try:
        chat = Chat.objects.get(id=chat_id, participantes=usuario_actual)
        if not chat.is_group:
            chat.participantes.remove(usuario_actual)
            if chat.participantes.count() == 0:
                chat.delete()
        else:
            chat.participantes.remove(usuario_actual)
            if chat.admin_grupo == usuario_actual:
                nuevo_admin = chat.participantes.first()
                if nuevo_admin:
                    chat.admin_grupo = nuevo_admin
                    chat.save()
                else:
                    chat.delete()
        return JsonResponse({"success": True, "message": "Chat eliminado"})
    except Chat.DoesNotExist:
        return JsonResponse({"error": "Chat no encontrado"}, status=404)


@require_POST
def silenciar_chat(request, chat_id):
    """
    Redirige al endpoint de notificaciones para silenciar al otro participante.
    En chats grupales silencia las notificaciones del grupo completo (futuro).
    """
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    try:
        chat = Chat.objects.get(id=chat_id, participantes=usuario_actual)
        data = json.loads(request.body) if request.body else {}

        if not chat.is_group:
            otro_usuario = chat.participantes.exclude(id=usuario_actual.id).first()
            if not otro_usuario:
                return JsonResponse({"error": "No se encontró el otro participante"}, status=404)

            from applications.notificaciones.models import ChatSilenciado
            ahora_silenciado = ChatSilenciado.toggle(usuario=usuario_actual, emisor=otro_usuario)

            return JsonResponse({
                "success": True,
                "silenciado": ahora_silenciado,
                "message": "Chat silenciado" if ahora_silenciado else "Notificaciones activadas",
            })
        else:
            # Grupos: por ahora devuelve éxito (implementar cuando sea necesario)
            return JsonResponse({
                "success": True,
                "silenciado": False,
                "message": "Función disponible próximamente para grupos",
            })

    except Chat.DoesNotExist:
        return JsonResponse({"error": "Chat no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def obtener_archivos_compartidos(request, chat_id):
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    try:
        chat = Chat.objects.get(id=chat_id, participantes=usuario_actual)
        mensajes_con_archivos = chat.mensajes_visibles_para_usuario(usuario_actual).exclude(
            archivo=""
        ).exclude(archivo__isnull=True)

        archivos = [{
            "id": m.id,
            "tipo": m.tipo_archivo or "unknown",
            "url": m.archivo.url if m.archivo else None,
            "nombre": m.nombre_archivo or m.contenido,
            "tamanio": m.tamanio_archivo,
            "autor": m.autor.nombre,
            "fecha": m.enviado.isoformat(),
        } for m in mensajes_con_archivos]

        return JsonResponse({"success": True, "archivos": archivos, "total": len(archivos)})
    except Chat.DoesNotExist:
        return JsonResponse({"error": "Chat no encontrado"}, status=404)

@require_POST
def salir_grupo(request, chat_id):
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    try:
        chat = Chat.objects.get(id=chat_id, participantes=usuario_actual)
    except Chat.DoesNotExist:
        return JsonResponse({"error": "Grupo no encontrado"}, status=404)

    if not chat.is_group:
        return JsonResponse({"error": "No es un grupo"}, status=400)

    es_admin = chat.admin_grupo == usuario_actual

    # Registrar el momento en que salió para no ver mensajes posteriores
    ChatVaciadoPorUsuario.objects.update_or_create(
        chat=chat,
        usuario=usuario_actual,
        defaults={"vaciado_en": timezone.now()}
    )

    # Quitar al usuario del grupo
    chat.participantes.remove(usuario_actual)

    participantes_restantes = chat.participantes.count()

    if participantes_restantes == 0:
        chat.delete()
        return JsonResponse({"success": True, "message": "Grupo eliminado por no tener participantes"})

    # Si era admin, transferir al participante con más antigüedad (menor id de unión)
    if es_admin:
        # El participante que lleva más tiempo es el que tiene el menor ID de usuario
        # entre los restantes (se unieron antes)
        nuevo_admin = chat.participantes.order_by("id").first()
        if nuevo_admin:
            chat.admin_grupo = nuevo_admin
            chat.save(update_fields=["admin_grupo"])

    return JsonResponse({
        "success": True,
        "message": "Saliste del grupo",
        "nuevo_admin": chat.admin_grupo.nombre if es_admin and chat.admin_grupo else None
    })


@require_POST
def eliminar_grupo(request, chat_id):
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    try:
        chat = Chat.objects.get(id=chat_id, participantes=usuario_actual)
    except Chat.DoesNotExist:
        return JsonResponse({"error": "Grupo no encontrado"}, status=404)

    if not chat.is_group:
        return JsonResponse({"error": "No es un grupo"}, status=400)

    if chat.admin_grupo != usuario_actual:
        return JsonResponse({"error": "Solo el admin puede eliminar el grupo"}, status=403)

    chat.delete()
    return JsonResponse({"success": True, "message": "Grupo eliminado"})

@require_POST
def agregar_participantes(request, chat_id):
    usuario_actual = obtener_usuario_actual(request)
    if not usuario_actual:
        return JsonResponse({"error": "Usuario no identificado"}, status=403)

    try:
        chat = Chat.objects.get(id=chat_id, participantes=usuario_actual)
    except Chat.DoesNotExist:
        return JsonResponse({"error": "Grupo no encontrado"}, status=404)

    if not chat.is_group:
        return JsonResponse({"error": "No es un grupo"}, status=400)

    if chat.admin_grupo != usuario_actual:
        return JsonResponse({"error": "Solo el admin puede agregar participantes"}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    ids = data.get("participante_ids", [])
    if not ids:
        return JsonResponse({"error": "No se especificaron participantes"}, status=400)

    # Solo amigos del admin que no están ya en el grupo
    try:
        amigos = Amistad.obtener_amigos(usuario_actual)
        amigos_ids = [a.id for a in amigos]
        ya_en_grupo = list(chat.participantes.values_list("id", flat=True))

        ids_validos = list(set(ids) & set(amigos_ids))
        if not ids_validos:
            return JsonResponse({"error": "Ningún usuario seleccionado es tu amigo"}, status=400)

        usuarios_a_agregar = Usuario.objects.filter(
            id__in=ids_validos
        ).exclude(id__in=ya_en_grupo)

        agregados = []
        for u in usuarios_a_agregar:
            chat.participantes.add(u)
            agregados.append({"id": u.id, "nombre": u.nombre})

        return JsonResponse({
            "success": True,
            "agregados": agregados,
            "message": f"{len(agregados)} participante(s) agregado(s)"
        })
    except Exception as e:
        logger.error(f"Error en agregar_participantes: {e}", exc_info=True)
        return JsonResponse({"error": f"Error interno: {str(e)}"}, status=500)