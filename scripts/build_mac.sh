#!/bin/bash
# Script para construir la aplicación ILO Tunnel Manager para macOS usando PyInstaller

echo "Limpiando builds anteriores..."
rm -rf build dist

echo "Generando archivo README.md en resources si no existe..."
mkdir -p ilo_tunnel/resources
if [ ! -f ilo_tunnel/resources/README.md ]; then
    echo "# Resources Directory" > ilo_tunnel/resources/README.md
fi

# Detectar el python correcto que tenga PyInstaller instalado
PYTHON=""
for candidate in python3.11 python3.12 python3.13 python3.10 python3; do
    if command -v "$candidate" > /dev/null 2>&1; then
        if "$candidate" -c "import PyInstaller" 2>/dev/null; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "No se encontró un Python con PyInstaller instalado."
    echo "Intentando instalar PyInstaller con pip3..."
    pip3 install pyinstaller
    PYTHON="python3"
    if ! "$PYTHON" -c "import PyInstaller" 2>/dev/null; then
        echo "❌ Error: No se pudo instalar PyInstaller. Instálalo manualmente:"
        echo "   pip3 install pyinstaller"
        exit 1
    fi
fi

echo "Usando Python: $PYTHON ($($PYTHON --version))"
echo "Construyendo aplicación macOS con PyInstaller..."
"$PYTHON" -m PyInstaller --clean -y ilo_tunnel_mac.spec

if [ -d "dist/ILO Tunnel Manager.app" ]; then
    echo ""
    echo "✅ Construcción completada con éxito!"
    echo "La aplicación se encuentra en: dist/ILO Tunnel Manager.app"
    echo ""
    echo "Para ejecutar la aplicación:"
    echo "  open 'dist/ILO Tunnel Manager.app'"
else
    echo ""
    echo "❌ Error en la construcción. Revisa los mensajes de error anteriores."
    exit 1
fi