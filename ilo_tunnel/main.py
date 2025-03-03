# ilo_tunnel/main.py
import sys
import platform
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDir

from .gui.main_window import ILOTunnelApp


def setup_environment():
    """Configura el entorno de ejecución de la aplicación"""
    # Asegurar que los directorios necesarios existen
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "ilo-tunnel")
    os.makedirs(config_dir, exist_ok=True)
    
    # Verificar si la aplicación se está ejecutando con los permisos necesarios
    if platform.system() == "Linux" or platform.system() == "Darwin":
        # En sistemas basados en Unix, comprobar si se está ejecutando como root
        if os.geteuid() != 0:
            print("ADVERTENCIA: La aplicación puede requerir permisos de administrador para crear túneles SSH.")
            print("Considera ejecutar con 'sudo' si experimentas problemas de permisos.")


def main():
    """Función principal de entrada"""
    # Configurar entorno
    setup_environment()
    
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("ILO Tunnel Manager")
    app.setOrganizationName("ILOTunnel")
    
    # Establecer estilo de la aplicación (opcional, usar el sistema por defecto)
    # app.setStyle("Fusion")
    
    # Crear y mostrar la ventana principal
    window = ILOTunnelApp()
    window.show()
    
    # Iniciar el bucle de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()