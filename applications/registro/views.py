from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Aprendiz, Bienestar, Instructor

def registro_view(request):
    if request.method == 'POST':
        rol = request.POST.get('rol')
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        numero_documento = request.POST.get('numero_documento')
        region = request.POST.get('region')
        contrasena = request.POST.get('password')

        try:
            if rol == 'aprendiz':
                Aprendiz.objects.create(
                    nombre=nombre,
                    tipo_documento=request.POST.get('tipo_documento'),
                    numero_documento=numero_documento,
                    email=email,
                    centro_formativo=request.POST.get('centro_formativo'),
                    jornada=request.POST.get('jornada'),
                    ficha=request.POST.get('ficha'),
                    region=region,
                    contrasena=contrasena
                )
                messages.success(request, '✅ Aprendiz registrado correctamente.')

            elif rol == 'bienestar':
                Bienestar.objects.create(
                    nombre=nombre,
                    tipo_documento=request.POST.get('tipo_documento'),
                    numero_documento=numero_documento,
                    email=email,
                    centro_formativo=request.POST.get('centro_formativo'),
                    region=region,
                    contrasena=contrasena
                )
                messages.success(request, '✅ Bienestar registrado correctamente.')

            elif rol == 'instructor':
                Instructor.objects.create(
                    nombre=nombre,
                    tipo_documento=request.POST.get('tipo_documento'),
                    numero_documento=numero_documento,
                    email=email,
                    centro_formativo=request.POST.get('centro_formativo'),
                    region=region,
                    contrasena=contrasena
                )
                messages.success(request, '✅ Instructor registrado correctamente.')

            else:
                messages.error(request, '❌ Rol no válido.')

            return redirect('registro:registro')


        except Exception as e:
            messages.error(request, f'⚠️ Error al registrar: {e}')
            # 👇 Este return faltaba
            return render(request, 'registrar.html')

    # Si no es POST, simplemente mostrar el formulario
    return render(request, 'registrar.html')
