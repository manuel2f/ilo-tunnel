#!/bin/bash

# Script para construir la aplicación ILO Tunnel
# Detecta el sistema operativo y construye en consecuencia

# Comprobar que PyInstaller está instalado
if ! pip show pyinstaller > /dev/null; then
    echo "PyInstaller no está instalado. Instalándolo..."
    pip install pyinstaller
fi

# Detectar sistema operativo
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Construyendo para Linux..."
    pyinstaller --name="ilo-tunnel-manager" --windowed \
                --add-data="ilo_tunnel/resources:resources" \
                --add-data="ilo_tunnel/ssh_manager.py:." \
                ilo_tunnel/main.py
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Construyendo para macOS..."
    pyinstaller --name="ILO Tunnel Manager" --windowed \
                --add-data="ilo_tunnel/resources:resources" \
                --add-data="ilo_tunnel/ssh_manager.py:." \
                ilo_tunnel/main.py
elif [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Construyendo para Windows..."
    pyinstaller --name="ILO Tunnel Manager" --windowed \
                --add-data="ilo_tunnel/resources;resources" \
                --add-data="ilo_tunnel/ssh_manager.py;." \
                ilo_tunnel/main.py
else
    echo "Sistema operativo no reconocido: $OSTYPE"
    exit 1
fi

echo "Construcción completada. El ejecutable se encuentra en el directorio 'dist'"
