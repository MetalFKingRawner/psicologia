# tests/management/commands/load_valores_data.py
import json
import os
from django.core.management.base import BaseCommand
from tests.models import TestValores, ParteTest, PreguntaValores, OpcionValores

class Command(BaseCommand):
    help = 'Carga los datos del Test de Valores de Allport desde un archivo JSON'
    
    def handle(self, *args, **options):
        # Ruta al archivo JSON (ajusta según tu estructura)
        json_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'estudio.json')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Crear el test principal
            test_info = data['test_info']
            test, created = TestValores.objects.get_or_create(
                nombre=test_info['nombre'],
                defaults={'autor': test_info['autor']}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Test creado: {test.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'Test ya existe: {test.nombre}'))
            
            # Crear partes del test
            primera_parte = ParteTest.objects.create(
                test=test,
                tipo='PRIMERA',
                instrucciones=data['instrucciones']['primera_parte']['sistema_puntuacion']
            )
            
            segunda_parte = ParteTest.objects.create(
                test=test,
                tipo='SEGUNDA',
                instrucciones=data['instrucciones']['segunda_parte']['sistema_puntuacion']
            )
            
            # Cargar preguntas de la primera parte
            for pagina_data in data['primera_parte']:
                for pregunta_data in pagina_data['preguntas']:
                    pregunta = PreguntaValores.objects.create(
                        parte=primera_parte,
                        texto=pregunta_data['pregunta'],
                        pagina=pagina_data['pagina']
                    )
                    for opcion_data in pregunta_data['columnas_opciones']:
                        OpcionValores.objects.create(
                            pregunta=pregunta,
                            letra=opcion_data['letra'],
                            texto=opcion_data['respuesta'],
                            columna=opcion_data['columna']
                        )
            
            # Cargar preguntas de la segunda parte
            for pagina_data in data['segunda_parte']:
                for pregunta_data in pagina_data['preguntas']:
                    pregunta = PreguntaValores.objects.create(
                        parte=segunda_parte,
                        texto=pregunta_data['pregunta'],
                        pagina=pagina_data['pagina']
                    )
                    for opcion_data in pregunta_data['columnas_opciones']:
                        OpcionValores.objects.create(
                            pregunta=pregunta,
                            letra=opcion_data['letra'],
                            texto=opcion_data['respuesta'],
                            columna=opcion_data['columna']
                        )
            
            self.stdout.write(self.style.SUCCESS('¡Datos cargados exitosamente!'))
            self.stdout.write(f'• Partes creadas: 2')
            self.stdout.write(f'• Preguntas totales: {PreguntaValores.objects.count()}')
            self.stdout.write(f'• Opciones totales: {OpcionValores.objects.count()}')
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Archivo estudio.json no encontrado'))
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f'Error en estructura JSON: clave faltante {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error inesperado: {str(e)}'))