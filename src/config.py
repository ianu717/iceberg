"""
config.py - Rutas y constantes compartidas del pipeline.
"""

from pathlib import Path

# Raíz del proyecto (un nivel por encima de src/).
ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"          # JSONs crudos de Open Data Euskadi             # dataset maestro procesado

# Query del catálogo de Open Data Euskadi que lista los datasets turísticos.
CATALOG_QUERY_URL = (
    "https://opendata.euskadi.eus/catalogo-datos/"
    "?r01kQry=tC:euskadi;tT:ds_recursos_turisticos;"
    "m:documentLanguage.EQ.es;pp:r01PageSize.100"
)

# Mapa editorial: dataset de origen -> (categoría Txoko, subcategoría).
CATEGORY_MAP = {
    # CULINARIO
    "restaurantes_asadores_sidrerias": ("Culinario", "Restaurantes / Asadores / Sidrerías"),
    "bares_pintxos": ("Culinario", "Bares de pintxos"),
    "pastelerias": ("Culinario", "Pastelerías y confiterías"),
    "gastronomia": ("Culinario", "Gastronomía general"),
    "platos_tipicos": ("Culinario", "Platos típicos"),
    "productos_tierra": ("Culinario", "Productos de la tierra"),
    "queserias": ("Culinario", "Queserías / Conserveras / Productores"),
    # CULTURAL
    "museos": ("Cultural", "Museos y centros de interpretación"),
    "patrimonio_edificios": ("Cultural", "Edificios religiosos / Castillos"),
    "patrimonio_cuevas": ("Cultural", "Cuevas y restos arqueológicos"),
    "recursos_culturales": ("Cultural", "Recursos culturales generales"),
    "auditorios": ("Cultural", "Auditorios"),
    "palacios_congresos": ("Cultural", "Palacios de congresos"),
    "hipodromos_estadios": ("Cultural", "Hipódromos y estadios"),
    # NATURALEZA
    "playas": ("Naturaleza", "Playas"),
    "espacios_naturales": ("Naturaleza", "Espacios naturales"),
    "parques_naturales": ("Naturaleza", "Parques naturales"),
    "rutas": ("Naturaleza", "Rutas y paseos"),
    "centros_btt": ("Naturaleza", "Centros BTT"),
    "puertos_pesqueros": ("Naturaleza", "Puertos pesqueros"),
    # OCIO
    "recursos_ocio": ("Ocio", "Ocio general"),
    "recursos_deportivos": ("Ocio", "Recursos deportivos"),
    "turismo_activo": ("Ocio", "Turismo activo (kayak, surf, escalada...)"),
    "alquiler_deportivo": ("Ocio", "Alquiler deportivo"),
    "golf": ("Ocio", "Golf"),
    "puertos_deportivos": ("Ocio", "Puertos deportivos / Náutica"),
    "palacios_hielo": ("Ocio", "Palacios de hielo"),
    "parques_atracciones": ("Ocio", "Parques de atracciones"),
    "aquariums": ("Ocio", "Aquariums"),
    "casinos": ("Ocio", "Casinos"),
    "turismo_salud": ("Ocio", "Turismo de salud / Spas / Balnearios"),
    # COMPRAS
    "zonas_compras": ("Compras", "Zonas de compras (comercio local)"),
    "recintos_feriales": ("Compras", "Recintos feriales"),
    # ALOJAMIENTO
    "hoteles": ("Alojamiento", "Hoteles"),
    "alojamientos_rurales": ("Alojamiento", "Alojamientos rurales"),
    "albergues": ("Alojamiento", "Albergues"),
    "campings": ("Alojamiento", "Campings"),
    # SERVICIOS
    "oficinas_turismo": ("Servicios", "Oficinas de turismo"),
    "destinos": ("Servicios", "Destinos turísticos (POIs generales)"),
}
