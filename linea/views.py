from django.shortcuts import render
from django.http import JsonResponse
from .models import Lineas, LineaRuta, LineasPuntos
from django.db.models import Prefetch

# Vista existente para el listado HTML (fase anterior)
def lista_lineas(request):
    """
    Muestra una lista de todas las líneas de transporte disponibles.
    """
    lineas = Lineas.objects.all()
    
    context = {
        'lineas': lineas,
        'titulo': 'Listado de Líneas de Transporte'
    }
    return render(request, 'linea/lista_lineas.html', context)

# ====================================================================
# NUEVA FUNCIÓN GET (API ENDPOINT) PARA OBTENER DATOS DE LA RUTA
# ====================================================================
def get_rutas_geojson(request):
    """
    Retorna todas las rutas y sus puntos en formato JSON optimizado para mapas.
    Formato de salida:
    [
        {
            "id": LineaRuta.id,
            "nombre_linea": "L001",
            "descripcion_ruta": "L001 Ruta Salida",
            "color": "#FF0000",
            "puntos": [ [lat, lng], ... ]
        },
        ...
    ]
    """
    try:
        # Usamos prefetch_related para cargar los LineasPuntos y la Lineas
        # con la menor cantidad de consultas a la base de datos posible.
        rutas = LineaRuta.objects.select_related('id_linea').prefetch_related(
            # Prefetch de los puntos de la ruta, ordenados por 'orden'
            Prefetch(
                'puntos_en_ruta', 
                queryset=LineasPuntos.objects.order_by('orden'),
                to_attr='puntos_ordenados'
            )
        ).all()

        listado_de_rutas = []

        for ruta in rutas:
            # 1. Obtener los puntos ordenados (ya precargados por Prefetch)
            puntos_coordenadas = []
            for punto_ruta in ruta.puntos_ordenados:
                # Agregamos las coordenadas como [latitud, longitud]
                puntos_coordenadas.append([
                    punto_ruta.latitud,
                    punto_ruta.longitud
                ])

            # 2. Obtener el nombre y color de la Línea
            # Asumo que el nombre y color vienen de la tabla Lineas
            # Si el color viene de LineaRuta, usa ruta.id_linea.color
            
            # Nota: Los datos CSV muestran el color en Lineas.csv, por eso accedemos a id_linea
            # Si Lineas.csv no fue cargado correctamente, el color puede ser incorrecto.
            
            # --- NOTA IMPORTANTE ---
            # El campo ColorLinea está en el CSV "DatosLineas.xls - Lineas.csv"
            # Asumo que tienes un campo `color` o `color_linea` en tu modelo Lineas
            # y que el campo `nombre` tiene el valor 'L001'.
            # Si el modelo Lineas no tiene 'color', esta parte fallará.
            
            color_hex = getattr(ruta.id_linea, 'color', '#000000') # Usamos un color por defecto si no existe
            
            ruta_data = {
                "id": ruta.id,
                "nombre_linea": ruta.id_linea.nombre.strip(), # Limpiamos espacios
                "descripcion_ruta": ruta.descripcion.strip(),
                "color": color_hex,
                "puntos": puntos_coordenadas,
            }
            listado_de_rutas.append(ruta_data)

        # Retornamos la lista de rutas como una respuesta JSON
        return JsonResponse(listado_de_rutas, safe=False)

    except Exception as e:
        # En caso de error, retornamos un mensaje de error 500
        return JsonResponse({'error': f'Ocurrió un error al procesar los datos: {str(e)}'}, status=500)
