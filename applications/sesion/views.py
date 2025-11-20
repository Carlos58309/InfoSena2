from django.shortcuts import render, redirect
from django.contrib import messages
from ..registro.models import Aprendiz, Instructor, Bienestar
from .models import Sesion

def login_view(request):
    if request.method == "POST":
        documento = request.POST.get("documento")
        password = request.POST.get("password")

        # Evita errores si no se ingresan datos
        if not documento or not password:
            messages.warning(request, "Por favor ingresa tu documento y contraseña.")
            return render(request, "login.html")

        # Buscar en Aprendiz
        aprendiz = Aprendiz.objects.filter(numero_documento=documento).first()
        if aprendiz and aprendiz.contrasena == password:
            Sesion.objects.create(numero_documento=documento, rol="Aprendiz", exito=True)
            messages.success(request, f"Bienvenido {aprendiz.nombre} (Aprendiz)")
            request.session["rol"] = "Aprendiz"
            request.session["nombre"] = aprendiz.nombre
            return redirect("sesion:dashboard")

        # Buscar en Instructor
        instructor = Instructor.objects.filter(numero_documento=documento).first()
        if instructor and instructor.contrasena == password:
            Sesion.objects.create(numero_documento=documento, rol="Instructor", exito=True)
            messages.success(request, f"Bienvenido {instructor.nombre} (Instructor)")
            request.session["rol"] = "Instructor"
            request.session["nombre"] = instructor.nombre
            return redirect("sesion:dashboard")

        # Buscar en Bienestar
        bienestar = Bienestar.objects.filter(numero_documento=documento).first()
        if bienestar and bienestar.contrasena == password:
            Sesion.objects.create(numero_documento=documento, rol="Bienestar", exito=True)
            messages.success(request, f"Bienvenido {bienestar.nombre} (Bienestar)")
            request.session["rol"] = "Bienestar"
            request.session["nombre"] = bienestar.nombre
            return redirect("sesion:dashboard")

        # Si no coincide nada
        Sesion.objects.create(numero_documento=documento, rol="Desconocido", exito=False)
        messages.error(request, "Número de documento o contraseña incorrectos.")
        return render(request, "login.html")

    # Si es un GET (solo mostrar el formulario)
    return render(request, "login.html")


def dashboard_view(request):
    # Si el usuario no tiene sesión, redirige al login
    if "rol" not in request.session:
        messages.warning(request, "Debes iniciar sesión para acceder al panel.")
        return redirect("sesion:login")

    contexto = {
        "nombre": request.session.get("nombre"),
        "rol": request.session.get("rol"),
    }
    return render(request, "dashboard.html", contexto)
