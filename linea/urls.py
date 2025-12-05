from django.urls import path
from . import views

app_name = 'linea'

urlpatterns = [
    # Vista HTML para listar líneas
    path('', views.lista_lineas, name='lista_lineas'),
    
    # API endpoint para obtener rutas en formato GeoJSON
    path('api/rutas/', views.get_rutas_geojson, name='get_rutas_geojson'),
]