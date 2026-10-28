#!/usr/bin/env bash
# Las revisiones de la CI, cada una en su archivo, para la evidencia de la semana 12.
#
# Desde la raíz del repositorio, con el entorno de Python del proyecto activado
# (pip install -e ".[api,dev,pipeline]") y `npm ci` hecho en app/:
#
#   bash deliveries/week12/pruebas/correr.sh deliveries/week12/pruebas/salidas
#
# Cada archivo empieza con el comando y termina con su código de salida. La prueba de humo
# levanta el API y la app si no están corriendo (app/playwright.config.ts). Las mil consultas
# de las propiedades tardan unos minutos más que el resto junto.
set -u

mkdir -p "${1:?falta la carpeta de salida}"
salida=$(cd "$1" && pwd)
cd "$(git rev-parse --show-toplevel)"

correr() {  # correr <archivo> <carpeta> <comando>
  local archivo=$1 carpeta=$2 comando=$3 codigo
  {
    echo "\$ $comando    # en $carpeta"
    echo
    (cd "$carpeta" && eval "$comando")
    codigo=$?
    echo
    echo "[código de salida: $codigo]"
  } > "$salida/$archivo" 2>&1
  echo "$archivo · $(tail -n 1 "$salida/$archivo")"
}

{
  # El árbol y no el hash del commit: el commit cambia de hash en cada clon que lo vuelve a hacer, el árbol no.
  echo "Árbol:   $(git rev-parse 'HEAD^{tree}'), el del commit «$(git log -1 --format=%s)»"
  echo "Fecha:   $(TZ=America/Lima date '+%Y-%m-%d %H:%M') (Lima)"
  echo "Sistema: $(uname -sm)"
  echo "Python:  $(python --version 2>&1) · $(ruff --version) · pytest $(python -c 'import pytest; print(pytest.__version__)') · hypothesis $(python -c 'import hypothesis; print(hypothesis.__version__)')"
  echo "Node:    $(node --version) · npm $(npm --version) · $(cd app && npx --no-install playwright --version)"
} > "$salida/00_entorno.txt"
echo "00_entorno.txt"

correr 01_ruff.txt . "ruff check . && ruff format --check ."
correr 02_pytest.txt . "python -m pytest -o addopts='' -v -p no:cacheprovider"
correr 03_propiedades_1000.txt . \
  "DREEMGO_PROPIEDADES=1000 python -m pytest -o addopts='' -v -p no:cacheprovider --hypothesis-show-statistics tests/test_propiedades.py"
correr 04_app_estilo_y_tipos.txt app "npm run revisar"
correr 05_app_tipos_del_contrato.txt app "npm run tipos && git diff --exit-code -- src/api/esquema.d.ts && echo 'src/api/esquema.d.ts sigue igual al contrato'"
correr 06_app_vitest.txt app "npx --no-install vitest run --reporter=verbose"
correr 07_app_construir.txt app "npm run build"
correr 08_humo_app_contra_api.txt app "npm run e2e"
