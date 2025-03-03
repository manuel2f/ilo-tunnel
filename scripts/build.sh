#!/bin/bash
# Script para construir la aplicación ILO Tunnel

# Comprobar que PyInstaller está instalado
if ! pip show pyinstaller > /dev/null; then
  echo "PyInstaller no está instalado. Instalándolo..."
  pip install pyinstaller
fi

# Detectar sistema operativo
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  echo "Construyendo para Linux..."
  pyinstaller --name="ilo-tunnel-manager" --windowed \
    --hidden-import=ilo_tunnel.models.server_types \
    --hidden-import=ilo_tunnel.models.profile \
    --hidden-import=ilo_tunnel.models.profile_manager \
    --hidden-import=ilo_tunnel.gui.dialogs \
    --hidden-import=ilo_tunnel.gui.widgets \
    --add-data="ilo_tunnel/resources:resources" \
    --add-data="ilo_tunnel/ssh_manager.py:." \
    ilo_tunnel/main.py

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Construyendo para macOS..."
    pyinstaller --name="ILO Tunnel Manager" --windowed\
        --hidden-import=ilo_tunnel.models.server_types \
        --hidden-import=ilo_tunnel.models.profile \
        --hidden-import=ilo_tunnel.models.profile_manager \
        --hidden-import=ilo_tunnel.gui.dialogs \
        --hidden-import=ilo_tunnel.gui.main_window \
        --hidden-import=ilo_tunnel.gui.widgets \
        --hidden-import=ilo_tunnel.config \
        --hidden-import=ilo_tunnel.ssh_manager \
        --add-data="ilo_tunnel/resources:resources" \
        --add-data="ilo_tunnel/models:ilo_tunnel/models" \
        --add-data="ilo_tunnel/gui:ilo_tunnel/gui" \
        --add-data="ilo_tunnel/utils:ilo_tunnel/utils" \
        --add-data="ilo_tunnel/config.py:ilo_tunnel" \
        --add-data="ilo_tunnel/ssh_manager.py:ilo_tunnel" \
        ilo_tunnel/main.py

elif [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "win32" ]]; then
  echo "Construyendo para Windows..."
  pyinstaller --name="ILO Tunnel Manager" --windowed \
    --hidden-import=ilo_tunnel.models.server_types \
    --hidden-import=ilo_tunnel.models.profile \
    --hidden-import=ilo_tunnel.models.profile_manager \
    --hidden-import=ilo_tunnel.gui.dialogs \
    --hidden-import=ilo_tunnel.gui.widgets \
    --add-data="ilo_tunnel/resources;resources" \
    ilo_tunnel/main.py

else
  echo "Sistema operativo no reconocido: $OSTYPE"
  exit 1
fi

echo "Construcción completada. El ejecutable se encuentra en el directorio 'dist'"