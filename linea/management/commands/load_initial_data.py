import csv
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from linea.models import Lineas, Puntos, LineaRuta, LineasPuntos

# Ruta a la carpeta 'data' dentro de la aplicación 'linea'
DATA_DIR = os.path.join(settings.BASE_DIR, 'linea', 'data')

def parse_float(value):
    """Convierte valores con coma decimal a float."""
    return float(value.replace(',', '.'))

class Command(BaseCommand):
    help = 'Importa datos iniciales desde archivos CSV a los modelos de la app "linea".'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('--- INICIANDO IMPORTACIÓN DE DATOS ---'))
        
        try:
            with transaction.atomic():
                # 1. LIMPIEZA DE DATOS PREVIOS (Recomendado para evitar duplicados)
                self.stdout.write(self.style.WARNING('Limpiando datos existentes...'))
                LineasPuntos.objects.all().delete()
                LineaRuta.objects.all().delete()
                Puntos.objects.all().delete()
                Lineas.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Limpieza completada.'))
                
                # Diccionarios de mapeo para mantener la relación de IDs originales a objetos creados
                lineas_map = {} # Mapeo de IdLinea original a objeto Lineas
                puntos_map = {} # Mapeo de IdPunto original a objeto Puntos
                linea_ruta_map = {} # Mapeo de IdLineaRuta original a objeto LineaRuta

                # =============================================================
                # 2. CARGA DE LINEAS
                # Archivo: Lineas.csv
                # Columnas: IdLinea,NombreLinea,ColorLinea,ImagenMicrobus,FechaCreacion
                # =============================================================
                self.stdout.write(self.style.NOTICE('1/4: Cargando Lineas...'))
                lineas_file_path = os.path.join(DATA_DIR, 'Lineas.csv')
                
                with open(lineas_file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    next(reader)  # Saltar la cabecera
                    
                    for row in reader:
                        # Limpiamos el nombre de espacios extra que vienen del Excel
                        nombre_limpio = row[1].strip()
                        color_linea = row[2].strip() if len(row) > 2 else '#000000'
                        
                        linea = Lineas.objects.create(
                            # Django generará el ID, solo necesitamos el nombre y color
                            nombre=nombre_limpio,
                            color=color_linea
                        )
                        # Guardamos el ID original del CSV para usarlo en las FK futuras
                        original_id = int(parse_float(row[0])) 
                        lineas_map[original_id] = linea
                self.stdout.write(self.style.SUCCESS(f'Lineas cargadas: {len(lineas_map)}'))
                
                # =============================================================
                # 3. CARGA DE PUNTOS
                # Archivo: Puntos.csv
                # Columnas: IdPunto,Latitud,Longitud,Descripcion
                # =============================================================
                self.stdout.write(self.style.NOTICE('2/4: Cargando Puntos...'))
                puntos_file_path = os.path.join(DATA_DIR, 'Puntos.csv')
                
                with open(puntos_file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    next(reader)  # Saltar la cabecera
                    
                    for row in reader:
                        original_id = int(parse_float(row[0]))
                        
                        punto = Puntos.objects.create(
                            latitud=parse_float(row[1]),
                            longitud=parse_float(row[2]),
                            descripcion=row[3].strip() 
                        )
                        puntos_map[original_id] = punto
                self.stdout.write(self.style.SUCCESS(f'Puntos cargados: {len(puntos_map)}'))

                # =============================================================
                # 4. CARGA DE LineaRuta (Requiere FK a Lineas)
                # Archivo: LineaRuta.csv
                # Columnas: IdLineaRuta,IdLinea,IdRuta,Descripcion,Distancia,Tiempo
                # =============================================================
                self.stdout.write(self.style.NOTICE('3/4: Cargando Rutas...'))
                rutas_file_path = os.path.join(DATA_DIR, 'LineaRuta.csv')
                
                with open(rutas_file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    next(reader)  # Saltar la cabecera
                    
                    for row in reader:
                        original_id_ruta = int(parse_float(row[0]))
                        original_id_linea = int(parse_float(row[1]))
                        
                        # USAMOS EL MAPEO: Convertimos el IdLinea del CSV al objeto Lineas
                        linea_obj = lineas_map.get(original_id_linea)
                        
                        if not linea_obj:
                            self.stdout.write(self.style.ERROR(f'FK error: Línea con ID {original_id_linea} no encontrada. Saltando ruta {original_id_ruta}.'))
                            continue
                            
                        ruta = LineaRuta.objects.create(
                            id_linea=linea_obj, # <-- ¡Clave Foránea correcta!
                            id_ruta=int(parse_float(row[2])),
                            descripcion=row[3].strip(),
                            distancia=parse_float(row[4]),
                            tiempo=parse_float(row[5])
                        )
                        linea_ruta_map[original_id_ruta] = ruta
                self.stdout.write(self.style.SUCCESS(f'Rutas cargadas: {len(linea_ruta_map)}'))
                
                # =============================================================
                # 5. CARGA DE LineasPuntos (Requiere FK a LineaRuta y Puntos)
                # Archivo: LineasPuntos.csv
                # Columnas: IdLineaPunto,IdLineaRuta,IdPunto,Orden,Latitud,Longitud,Distancia,Tiempo
                # =============================================================
                self.stdout.write(self.style.NOTICE('4/4: Cargando Puntos de Rutas...'))
                lineas_puntos_file_path = os.path.join(DATA_DIR, 'LineasPuntos.csv')
                
                puntos_enrutados_count = 0
                with open(lineas_puntos_file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    next(reader)  # Saltar la cabecera
                    
                    # Usamos bulk_create para insertar masivamente (mejor rendimiento)
                    new_lineas_puntos = []
                    
                    for row in reader:
                        # Mapeo de IDs originales a objetos
                        original_id_linea_ruta = int(parse_float(row[1]))
                        original_id_punto = int(parse_float(row[2]))
                        
                        # USAMOS LOS MAPEOS:
                        ruta_obj = linea_ruta_map.get(original_id_linea_ruta)
                        punto_obj = puntos_map.get(original_id_punto)
                        
                        if not ruta_obj or not punto_obj:
                            continue
                            
                        linea_punto = LineasPuntos(
                            id_linea_ruta=ruta_obj, # <-- ¡Clave Foránea correcta!
                            id_punto=punto_obj,     # <-- ¡Clave Foránea correcta!
                            orden=int(parse_float(row[3])),
                            latitud=parse_float(row[4]),
                            longitud=parse_float(row[5]),
                            distancia=parse_float(row[6]),
                            tiempo=parse_float(row[7])
                        )
                        new_lineas_puntos.append(linea_punto)
                        puntos_enrutados_count += 1

                    LineasPuntos.objects.bulk_create(new_lineas_puntos)
                        
                self.stdout.write(self.style.SUCCESS(f'Puntos de Rutas cargados: {puntos_enrutados_count}'))

            self.stdout.write(self.style.SUCCESS('--- ¡IMPORTACIÓN COMPLETADA CON ÉXITO! ---'))

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f'ERROR: Archivo no encontrado. Asegúrate de que los CSV estén en "linea/data/". Falta: {e.filename}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocurrió un error inesperado durante la importación: {e}'))