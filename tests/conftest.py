"""Las pruebas no usan ni el almacén de eventos ni la clave que tenga en su entorno quien las corre."""

import os

for variable in ("DREEMGO_TABLA_EVENTOS", "DREEMGO_EVENTOS_ARCHIVO", "DREEMGO_CLAVE_PUBLICADOR"):
    os.environ.pop(variable, None)
