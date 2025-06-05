import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.db import transaction
from .models import TestValores, ParteTest, PreguntaValores, OpcionValores, ResultadoValores
from .models import TestDomino, ProblemaDomino
from users.models import CustomUser
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

def inicio_test_valores(request):
    #test = TestValores.objects.get(nombre="Test de Valores de Allport")
    #primera_parte = ParteTest.objects.get(test=test, tipo='PRIMERA')
    try:
        test = TestValores.objects.get(nombre="Test de Valores de Allport")
        primera_parte = ParteTest.objects.get(test=test, tipo='PRIMERA')
    except (TestValores.DoesNotExist, ParteTest.DoesNotExist):
        # Manejo de error más amigable
        return render(request, 'tests/error.html', {
            'message': 'Configuración de prueba no encontrada'
        })
    return render(request, 'tests/inicio_test_valores.html', {
        'test': test,
        'primera_parte': primera_parte
    })

def inicio_segundo_test_valores(request):
    #test = TestValores.objects.get(nombre="Test de Valores de Allport")
    #segunda_parte = ParteTest.objects.get(test=test, tipo='SEGUNDA')
    test = get_object_or_404(TestValores, nombre="Test de Valores de Allport")
    segunda_parte = get_object_or_404(ParteTest, test=test, tipo='SEGUNDA')
    
    return render(request, 'tests/inicio_segunda_parte_valores.html', {
        'test': test,
        'segunda_parte': segunda_parte
    })

def primera_parte_valores(request):
    #test = TestValores.objects.get(nombre="Test de Valores de Allport")
    #primera_parte = ParteTest.objects.get(test=test, tipo='PRIMERA')
    test = get_object_or_404(TestValores, nombre="Test de Valores de Allport")
    primera_parte = get_object_or_404(ParteTest, test=test, tipo='PRIMERA')
    preguntas = PreguntaValores.objects.filter(parte=primera_parte).order_by('id')
    
    if request.method == 'POST':
        # Almacenar respuestas como diccionario de listas
        respuestas = {}
        for key in request.POST:
            if key.startswith('puntos_p'):
                # Convertir a entero y almacenar
                try:
                    respuestas[key] = int(request.POST[key])
                except ValueError:
                    respuestas[key] = 0
        # Guardar respuestas en la sesión
        request.session['primera_parte_respuestas'] = respuestas
        print("Respuestas primera parte guardadas:", respuestas)  # Debug
        return redirect('inicio_segundo_test_valores')
    
    return render(request, 'tests/primera_parte_valores.html', {
        'test': test,
        'parte': primera_parte,
        'preguntas': preguntas,
        'total_preguntas': preguntas.count()
    })

def segunda_parte_valores(request):
    #test = TestValores.objects.get(nombre="Test de Valores de Allport")
    #segunda_parte = ParteTest.objects.get(test=test, tipo='SEGUNDA')
    test = get_object_or_404(TestValores, nombre="Test de Valores de Allport")
    segunda_parte = get_object_or_404(ParteTest, test=test, tipo='SEGUNDA')
    preguntas = PreguntaValores.objects.filter(parte=segunda_parte).order_by('id')
    
    if request.method == 'POST':
        respuestas = {}
        for key in request.POST:
            if key.startswith('puntos_p'):
                try:
                    respuestas[key] = int(request.POST[key])
                except ValueError:
                    respuestas[key] = 0
        # Guardar respuestas en la sesión
        request.session['segunda_parte_respuestas'] = respuestas
        print("Respuestas segunda parte guardadas:", respuestas)  # Debug
        return redirect('calcular_resultados_valores')
    
    return render(request, 'tests/segunda_parte_valores.html', {
        'test': test,
        'parte': segunda_parte,
        'preguntas': preguntas,
        'total_preguntas': preguntas.count()
    })


def calcular_resultados_valores(request):
    if not request.user.is_authenticated:
        return redirect('core_login')
    
    try:
        # Cargar estructura del test desde JSON
        json_path = settings.BASE_DIR / 'estudio.json'
        with open(json_path, 'r', encoding='utf-8') as f:
            estudio = json.load(f)
        
        # Obtener respuestas de la sesión
        primera_parte = request.session.get('primera_parte_respuestas', {})
        segunda_parte = request.session.get('segunda_parte_respuestas', {})

        # DEBUG: Verificar respuestas recibidas
        print("Respuestas primera parte:", primera_parte)
        print("Respuestas segunda parte:", segunda_parte)
        
        # Obtener género del usuario
        genero_usuario = request.user.gender if hasattr(request.user, 'gender') else 'M'

        # Inicializar acumuladores
        totales_por_pagina = {}
        resultados_valores = {
            'Teórico': 0,
            'Económico': 0,
            'Estético': 0,
            'Social': 0,
            'Político': 0,
            'Religioso': 0
        }
        
        # Obtener mapeo de páginas
        mapeo_paginas = None
        for item in estudio['criterios_calificacion']['procedimiento']:
            if isinstance(item, dict):
                mapeo_paginas = item
                break
        
        if not mapeo_paginas:
            raise ValueError("No se encontró el mapeo de páginas en el JSON")
        
        # 1. Procesar primera parte
        print("="*50)
        print("PRIMERA PARTE")
        print("="*50)
        for pagina_data in estudio['primera_parte']:
            num_pagina = pagina_data['pagina']
            clave_pagina = f"pagina_{num_pagina}"
            totales_por_pagina[clave_pagina] = {'R': 0.0, 'S': 0.0, 'T': 0.0, 'X': 0.0, 'Y': 0.0, 'Z': 0.0}

            print(f"\nPágina {num_pagina}:")
            
            for pregunta in pagina_data['preguntas']:
                pregunta_id = pregunta['id']
                key_a = f'puntos_p{pregunta_id}_a'
                key_b = f'puntos_p{pregunta_id}_b'
                
                # Obtener valores como float
                try:
                    puntos_a = float(primera_parte.get(key_a, 0))
                except (TypeError, ValueError):
                    puntos_a = 0.0
                
                try:
                    puntos_b = float(primera_parte.get(key_b, 0))
                except (TypeError, ValueError):
                    puntos_b = 0.0
                
                # Detectar pregunta omitida
                if puntos_a == 0 and puntos_b == 0:
                    puntos_a = 1.5
                    puntos_b = 1.5
                
                # Sumar a las columnas correspondientes
                for opcion in pregunta['columnas_opciones']:
                    columna = opcion['columna']
                    if opcion['letra'] == 'a':
                        totales_por_pagina[clave_pagina][columna] += puntos_a
                    else:
                        totales_por_pagina[clave_pagina][columna] += puntos_b

            # Imprimir totales de la página
            for col, val in totales_por_pagina[clave_pagina].items():
                print(f"{col}: {val:.1f}")
        
        # 2. Procesar segunda parte
        print("\n" + "="*50)
        print("SEGUNDA PARTE")
        print("="*50)
        for pagina_data in estudio['segunda_parte']:
            num_pagina = pagina_data['pagina']
            clave_pagina = f"pagina_{num_pagina}"
            totales_por_pagina[clave_pagina] = {'R': 0.0, 'S': 0.0, 'T': 0.0, 'X': 0.0, 'Y': 0.0, 'Z': 0.0}

            # Identificar preguntas de género (14 y 15)
            pregunta_14 = None
            pregunta_15 = None
            otras_preguntas = []
            
            for pregunta in pagina_data['preguntas']:
                if pregunta['id'] == 44:
                    pregunta_14 = pregunta
                elif pregunta['id'] == 45:
                    pregunta_15 = pregunta
                else:
                    otras_preguntas.append(pregunta)
            
            # Procesar preguntas normales
            for pregunta in otras_preguntas:
                procesar_pregunta_segunda_parte(pregunta, segunda_parte, totales_por_pagina[clave_pagina])
            
            # Procesar preguntas de género según corresponda
            if genero_usuario == 'M':  # Masculino
                if pregunta_14:
                    procesar_pregunta_segunda_parte(pregunta_14, segunda_parte, totales_por_pagina[clave_pagina])
            else:  # Femenino u otro
                if pregunta_15:
                    procesar_pregunta_segunda_parte(pregunta_15, segunda_parte, totales_por_pagina[clave_pagina])
            # Imprimir totales de la página
            print(f"\nPágina {num_pagina}:")
            for col, val in totales_por_pagina[clave_pagina].items():
                print(f"{col}: {val:.1f}")
        
        # 3. Mapear columnas a valores y sumar
        print("\n" + "="*50)
        print("SUMA POR VALORES (ANTES DE CORRECCIONES)")
        print("="*50)
        for clave_pagina, totales in totales_por_pagina.items():
            if clave_pagina in mapeo_paginas:
                mapeo = mapeo_paginas[clave_pagina]
                for columna, valor in totales.items():
                    nombre_valor = mapeo[columna]
                    resultados_valores[nombre_valor] += valor

                    # Imprimir contribución de cada columna
                    print(f"{clave_pagina} - {columna} -> {nombre_valor}: {valor:.1f}")
        
        # Imprimir resultados antes de correcciones
        print("\n" + "="*50)
        print("RESULTADOS ANTES DE CORRECCIONES")
        print("="*50)
        for valor, puntuacion in resultados_valores.items():
            print(f"{valor}: {puntuacion:.1f}")

        # 4. Aplicar correcciones
        correcciones = {
            'Teórico': -4,
            'Económico': -5,
            'Estético': 6,
            'Social': -1,
            'Político': 3,
            'Religioso': 1
        }

        # 5. Clasificar cada valor según los rangos del cuadro físico
        clasificaciones = {}
        colores = {}
        
        # Definición de rangos según el cuadro físico
        rangos_valores = {
            'Teórico': {'muy_bajo': 30, 'bajo': 34, 'alto': 45, 'muy_alto': 50},
            'Económico': {'muy_bajo': 28, 'bajo': 35, 'alto': 45, 'muy_alto': 51},
            'Estético': {'muy_bajo': 30, 'bajo': 35, 'alto': 46, 'muy_alto': 52},
            'Social': {'muy_bajo': 29, 'bajo': 34, 'alto': 44, 'muy_alto': 49},
            'Político': {'muy_bajo': 31, 'bajo': 35, 'alto': 48, 'muy_alto': 50},
            'Religioso': {'muy_bajo': 26, 'bajo': 33, 'alto': 48, 'muy_alto': 57},
        }
        
        significado_clinico = {
            'MUY BAJO': "Significativamente por debajo de la norma poblacional",
            'BAJO': "Por debajo del promedio poblacional",
            'NORMAL': "Dentro del rango esperado para la población",
            'ALTO': "Por encima del promedio poblacional",
            'MUY ALTO': "Significativamente por encima de la norma poblacional",
        }
        
        for valor, puntuacion in resultados_valores.items():
            rangos = rangos_valores[valor]
            
            if puntuacion < rangos['muy_bajo']:
                clasif = "MUY BAJO"
                color = "#dc3545"  # Rojo
            elif puntuacion < rangos['bajo']:
                clasif = "BAJO"
                color = "#ffc107"  # Amarillo
            elif puntuacion > rangos['muy_alto']:
                clasif = "MUY ALTO"
                color = "#0dcaf0"  # Turquesa
            elif puntuacion > rangos['alto']:
                clasif = "ALTO"
                color = "#198754"  # Verde
            else:
                clasif = "NORMAL"
                color = "#2a4d6e"  # Azul claro
                
            clasificaciones[valor] = {
                'clasificacion': clasif,
                'color': color,
                'significado': significado_clinico[clasif]
            }
        
        for valor, correccion in correcciones.items():
            resultados_valores[valor] += correccion

        # Imprimir resultados después de correcciones
        print("\n" + "="*50)
        print("RESULTADOS DESPUÉS DE CORRECCIONES")
        print("="*50)
        for valor, puntuacion in resultados_valores.items():
            print(f"{valor}: {puntuacion:.1f}")
        
        # 6. Preparar datos para la plantilla
        valores_ordenados = sorted(
            resultados_valores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        valor_dominante = valores_ordenados[0][0]
        
        # Obtener descripción del valor dominante
        descripcion_valor = next(
            (v['descripcion'] for v in estudio['interpretacion_valores']['valores'] 
            if v['nombre'] == valor_dominante
        ))
        
        meta_valor = next(
            (v['meta'] for v in estudio['interpretacion_valores']['valores'] 
            if v['nombre'] == valor_dominante
        ))
        
        # 5. Guardar resultados en la base de datos
        with transaction.atomic():
            test = TestValores.objects.get(nombre="Test de Valores de Allport")
            usuario = CustomUser.objects.get(id=request.user.id)
            
            resultado = ResultadoValores(
                usuario=usuario,
                test=test,
                teorico=resultados_valores['Teórico'],
                economico=resultados_valores['Económico'],
                estetico=resultados_valores['Estético'],
                social=resultados_valores['Social'],
                politico=resultados_valores['Político'],
                religioso=resultados_valores['Religioso'],
                clasificaciones=clasificaciones,
                valor_dominante=valor_dominante,
                descripcion_dominante=descripcion_valor,
                meta_dominante=meta_valor,
                rangos_valores=rangos_valores
            )
            resultado.save()
        
        # 6. Preparar datos para la plantilla
        #valores_ordenados = sorted(
        #    resultados_valores.items(), 
        #    key=lambda x: x[1], 
        #    reverse=True
        #)
        
        #valor_dominante = valores_ordenados[0][0]
        
        # Obtener descripción del valor dominante
        #descripcion_valor = next(
        #    (v['descripcion'] for v in estudio['interpretacion_valores']['valores'] 
        #    if v['nombre'] == valor_dominante
        #))
        
        #meta_valor = next(
        #    (v['meta'] for v in estudio['interpretacion_valores']['valores'] 
        #    if v['nombre'] == valor_dominante
        #))
        
        # Guardar en sesión para mostrar en resultados
        request.session['resultados_valores'] = {
            'valores': resultados_valores,
            'dominante': valor_dominante,
            'descripcion': descripcion_valor,
            'meta': meta_valor,
            'clasificaciones': clasificaciones,  # Nuevo dato
            'rangos_valores': rangos_valores,    # Nuevo dato
        }
        
        # Limpiar respuestas almacenadas
        request.session.pop('primera_parte_respuestas', None)
        request.session.pop('segunda_parte_respuestas', None)

        # Guardar solo el ID en la sesión
        request.session['resultado_id'] = resultado.id
        
        return redirect('mostrar_resultados_valores')
    
    except Exception as e:
        logger.exception("Error al calcular resultados")
        return render(request, 'error.html', {'error': str(e)})

def procesar_pregunta_segunda_parte(pregunta, respuestas, totales_pagina):
    pregunta_id = pregunta['id']
    puntos = {}
    omitida = True
    
    for opcion in pregunta['columnas_opciones']:
        letra = opcion['letra']
        key = f'puntos_p{pregunta_id}_{letra}'
        
        try:
            valor = float(respuestas.get(key, 0))
        except (TypeError, ValueError):
            valor = 0.0
        
        puntos[letra] = valor
        if valor != 0:
            omitida = False
    
    # Si omitió la pregunta, asignar 2.5 a cada opción
    if omitida:
        for opcion in pregunta['columnas_opciones']:
            puntos[opcion['letra']] = 2.5
    
    # Sumar a las columnas correspondientes
    for opcion in pregunta['columnas_opciones']:
        columna = opcion['columna']
        totales_pagina[columna] += puntos[opcion['letra']]

def mostrar_resultados_valores(request):
    resultados = request.session.pop('resultados_valores', None)
    resultado_id = request.session.get('resultado_id')
    
    if not resultados:
        return redirect('home')
    
    try:
        resultado = ResultadoValores.objects.get(id=resultado_id)
    except ResultadoValores.DoesNotExist:
        return redirect('home')
    
    # Preparar datos para la gráfica
    valores = ['Teórico', 'Económico', 'Estético', 'Social', 'Político', 'Religioso']
    puntuaciones = [resultados['valores'][v] for v in valores]

    # Preparar colores para la gráfica
    colores_grafica = [resultados['clasificaciones'][v]['color'] for v in valores]
    
    context = {
        'valores': resultados['valores'],
        'dominante': resultados['dominante'],
        'descripcion': resultados['descripcion'],
        'meta': resultados['meta'],
        'clasificaciones': resultados['clasificaciones'],
        'rangos_valores': resultados['rangos_valores'],
        'valores_grafica': valores,
        'puntuaciones_grafica': puntuaciones,
        'colores_grafica_json': json.dumps(colores_grafica),
        'rangos_valores_json': json.dumps(resultados['rangos_valores']),
        'resultado_id': resultado_id,  # Pasar el ID para el PDF
    }
    
    response = render(request, 'tests/resultados_valores.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def generar_pdf_valores(request, resultado_id):
    # Recuperar resultados de la sesión
    try:
        resultado = ResultadoValores.objects.get(id=resultado_id)
    except ResultadoValores.DoesNotExist:
        return HttpResponse("No hay resultados disponibles", status=404)
    
    # Preparar datos para el gráfico
    valoress = ['Teórico', 'Económico', 'Estético', 'Social', 'Político', 'Religioso']
    puntuaciones = [
        resultado.teorico,
        resultado.economico,
        resultado.estetico,
        resultado.social,
        resultado.politico,
        resultado.religioso
    ]
    
    # Generar gráfico radar con matplotlib
  
    # Calcular ángulos para cada eje
    num_vars = len(valoress)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    puntuaciones += puntuaciones[:1]  # Cerrar el círculo
    angles += angles[:1]  # Cerrar los ángulos
    
    plt.figure(figsize=(8, 8), facecolor='white')
    ax = plt.subplot(111, polar=True, facecolor='#f8f9fa')

    # Colores y estilos
    ax.spines['polar'].set_visible(False)
    ax.grid(color='gray', linestyle='-', linewidth=0.5, alpha=0.3)

    # Línea y relleno
    ax.plot(angles, puntuaciones, color='#3A7D7D', linewidth=2, marker='o', 
            markersize=8, markerfacecolor='#3A7D7D', markeredgecolor='white', 
            markeredgewidth=1.5)
            
    ax.fill(angles, puntuaciones, color='#3A7D7D', alpha=0.1)

    # Etiquetas
    plt.xticks(angles[:-1], valoress, fontsize=10, fontweight='bold', color='#333')
    #plt.yticks([], [])  # Ocultar valores radiales

    # Título
    plt.title('Perfil de Valores', fontsize=14, fontweight='bold', pad=20)
    
    # Guardar en buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    plt.close()
    buffer.seek(0)
    
    # Convertir a base64
    image_png = buffer.getvalue()
    buffer.close()
    grafico_base64 = base64.b64encode(image_png).decode('utf-8')

    # Preparar el contexto
    valores = {
        'Teórico': resultado.teorico,
        'Económico': resultado.economico,
        'Estético': resultado.estetico,
        'Social': resultado.social,
        'Político': resultado.politico,
        'Religioso': resultado.religioso,
    }

    context = {
        'valores': valores,
        'dominante': resultado.valor_dominante,
        'descripcion': resultado.descripcion_dominante,
        'meta': resultado.meta_dominante,
        'clasificaciones': resultado.clasificaciones,
        'rangos_valores': resultado.rangos_valores,
        'grafico_base64': grafico_base64,  # Imagen del gráfico
        'static_path': os.path.join(settings.BASE_DIR, 'psycho_platform', 'static'),
        'resultado_id': resultado_id
    }
    
    # Cargar la plantilla
    template_path = 'tests/reporte_valores.html'
    template = get_template(template_path)
    html = template.render(context)
    
    # Crear respuesta HTTP con el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_valores.pdf"'
    
    # Generar PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    # Si hay errores, mostramos un mensaje
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF: %s' % html)
    return response

def inicio_domino(request):
    test = get_object_or_404(TestDomino, nombre="Test de Dominó D-48")
    #test = TestDomino.objects.get(nombre="Test de Dominó D-48")
    return render(request, 'tests/inicio_domino.html', {
        'test': test
    })

def test_domino(request):
    # Crear lista de números de problemas matriciales
    numeros_problemas = list(range(1, 25))  # Problemas 1-24
    numeros_problemas.extend([35, 36])      # Problemas 35-36
    numeros_problemas.extend(range(41, 49)) # Problemas 41-48

    # Obtener problemas y preparar sus matrices
    problemas = ProblemaDomino.objects.filter(
        tipo='MATRIZ',
        numero__in=numeros_problemas
    ).order_by('numero')
    
    problemas_preparados = []
    for problema in problemas:
        # Crear matriz vacía
        matriz = [[None for _ in range(problema.matriz_columnas)] 
                  for _ in range(problema.matriz_filas)]
        
        # Llenar matriz con fichas
        for ficha_data in problema.fichas:
            fila = ficha_data['fila']
            columna = ficha_data['columna']
            matriz[fila][columna] = ficha_data
        
        problemas_preparados.append({
            'obj': problema,
            'matriz': matriz
        })
    
    return render(request, 'tests/test_domino.html', {
        'problemas_preparados': problemas_preparados
    })

def detalle_problema_domino(request, problema_id):
    problema = get_object_or_404(ProblemaDomino, id=problema_id)
    
    # Preparar la matriz de fichas
    matriz = [[None for _ in range(problema.matriz_columnas)] 
              for _ in range(problema.matriz_filas)]
    
    for ficha_data in problema.fichas:
        fila = ficha_data['fila']
        columna = ficha_data['columna']
        matriz[fila][columna] = ficha_data
    
    return render(request, 'tests/detalle_problema_domino.html', {
        'problema': problema,
        'matriz': matriz
    })

#def resultados_valores(request):
    # Esta vista la implementaremos después de capturar las respuestas
#    return render(request, 'tests/resultados_valores.html')
