import logging

def obtener_logger(nombre_modulo: str):
    """Configura un logger estandarizado para DataOps."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] [%(name)s]: %(message)s'
    )
    return logging.getLogger(nombre_modulo)