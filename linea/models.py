from django.db import models

# =================================================================
# TABLA PRINCIPAL: Lineas
# Corresponde a la entidad principal que agrupa las rutas.
# =================================================================

class Lineas(models.Model):
    # IdLinea : integer «PK» - Clave Primaria, se gestiona automáticamente por Django.
    # Django automáticamente crea el campo 'id' (IdLinea) como PK de tipo BigAutoField.
    
    nombre = models.CharField(
        max_length=255, 
        verbose_name="Nombre de la Línea",
        help_text="Nombre descriptivo de la línea de transporte."
    )
    
    color = models.CharField(
        max_length=7,  # Para colores hex como #FF0000
        verbose_name="Color de la Línea",
        help_text="Color hexadecimal para representar la línea en mapas.",
        default="#000000"
    )

    class Meta:
        verbose_name = "Línea"
        verbose_name_plural = "Líneas"
        # Opcional: define el nombre de la tabla en PostgreSQL si no quieres el nombre por defecto 'linea_lineas'
        # db_table = 'Lineas' 
        
    def __str__(self):
        return self.nombre

# =================================================================
# TABLA DE RELACIÓN 1: LineaRuta
# Representa las "rutas" asociadas a una línea.
# =================================================================
class LineaRuta(models.Model):
    # IdLineaRuta : integer «PK» - Clave Primaria.
    
    # IdLinea : integer «FK» - Relación con la tabla Lineas
    id_linea = models.ForeignKey(
        Lineas, 
        on_delete=models.CASCADE, 
        related_name='rutas', 
        verbose_name="Línea Asociada"
    )
    
    # IdRuta : integer - Identificador de la ruta (podría ser un campo simple o una FK a otra tabla de Rutas)
    # Asumiendo que IdRuta es un identificador simple dentro de este modelo:
    id_ruta = models.IntegerField(
        verbose_name="ID de Ruta",
        help_text="Identificador único para esta ruta dentro de la línea."
    )
    
    descripcion = models.CharField(
        max_length=500, 
        verbose_name="Descripción de la Ruta"
    )
    
    distancia = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Distancia (km)"
    )
    
    tiempo = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="Tiempo Estimado (horas)"
    )

    class Meta:
        verbose_name = "Ruta de Línea"
        verbose_name_plural = "Rutas de Línea"
        # Asegura que la combinación de Línea y Ruta sea única
        unique_together = ('id_linea', 'id_ruta')
        
    def __str__(self):
        return f"Ruta {self.id_ruta} de Línea: {self.id_linea.nombre}"

# =================================================================
# TABLA INDEPENDIENTE: Puntos
# Representa puntos geográficos genéricos.
# =================================================================
class Puntos(models.Model):
    # IdPunto : integer «PK» - Clave Primaria.
    
    latitud = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        verbose_name="Latitud"
    )
    
    longitud = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        verbose_name="Longitud"
    )
    
    descripcion = models.CharField(
        max_length=500, 
        null=True, 
        blank=True, 
        verbose_name="Descripción del Punto"
    )

    class Meta:
        verbose_name = "Punto Geográfico"
        verbose_name_plural = "Puntos Geográficos"
        
    def __str__(self):
        return f"Punto ({self.latitud}, {self.longitud})"

# =================================================================
# TABLA DE RELACIÓN 2: LineasPuntos (Tabla Intermedia)
# Conecta la ruta específica (LineaRuta) con los puntos que la componen (Puntos).
# Esta es una relación Many-to-Many "Through" con campos extra.
# =================================================================
class LineasPuntos(models.Model):
    # IdLineaPunto : integer «PK» - Clave Primaria.
    
    # IdLineaRuta : integer «FK» - Relación con la tabla LineaRuta (la ruta específica)
    id_linea_ruta = models.ForeignKey(
        LineaRuta, 
        on_delete=models.CASCADE, 
        related_name='puntos_en_ruta',
        verbose_name="Ruta"
    )
    
    # IdPunto : integer «FK» - Relación con la tabla Puntos (el punto geográfico)
    id_punto = models.ForeignKey(
        Puntos, 
        on_delete=models.CASCADE, 
        related_name='referencias_en_rutas',
        verbose_name="Punto"
    )
    
    orden = models.IntegerField(
        verbose_name="Orden en la Ruta",
        help_text="Posición secuencial del punto dentro de la ruta (1, 2, 3...)."
    )
    
    # Los siguientes campos parecen ser redundantes ya que el Punto ya tiene Latitud/Longitud, 
    # pero los incluimos si son específicos de este paso de la ruta. 
    # Si son los mismos que Puntos, podría considerar borrarlos.
    latitud = models.DecimalField(max_digits=10, decimal_places=7)
    longitud = models.DecimalField(max_digits=10, decimal_places=7)
    
    distancia = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Distancia al siguiente punto",
        help_text="Distancia desde este punto hasta el siguiente en la ruta."
    )
    
    tiempo = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name="Tiempo de recorrido",
        help_text="Tiempo estimado de recorrido desde el punto anterior hasta este."
    )

    class Meta:
        verbose_name = "Punto en Línea/Ruta"
        verbose_name_plural = "Puntos en Líneas/Rutas"
        # Asegura que un punto en una ruta tenga un orden único
        unique_together = ('id_linea_ruta', 'orden')
        # También puedes asegurar que un punto no se repita en la misma ruta si es necesario:
        # unique_together = ('id_linea_ruta', 'id_punto')
        ordering = ['orden'] # Ordena por defecto por la secuencia

    def __str__(self):
        return f"Punto {self.orden} en Ruta {self.id_linea_ruta.id_ruta}"