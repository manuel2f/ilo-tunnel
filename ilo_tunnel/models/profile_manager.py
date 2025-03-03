# ilo_tunnel/models/profile_manager.py
import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from PyQt6.QtCore import QSettings
from ..models.profile import ConnectionProfile
from ..config import Config


class ProfileManager:
    """Gestor de perfiles de conexión con soporte para carpetas"""

    def __init__(self):
        self.settings = QSettings("ILOTunnel", "ILOTunnelApp")
        self.config = Config()

    def get_profiles(self, folder: Optional[str] = None) -> Dict[str, List[dict]]:
        """
        Obtiene todos los perfiles o los perfiles de una carpeta específica

        Args:
            folder: Nombre de la carpeta (opcional)

        Returns:
            Un diccionario de carpetas con listas de perfiles o una lista de perfiles
        """
        profiles_json = self.settings.value("connection_profiles", "{}")
        try:
            profiles_data = json.loads(profiles_json)

            # Si no hay estructura de carpetas, convertir al nuevo formato
            if isinstance(profiles_data, list):
                profiles_data = {"DEFAULT": profiles_data}
                self.save_profiles_data(profiles_data)

            if folder:
                return profiles_data.get(folder, [])
            else:
                return profiles_data
        except Exception as e:
            print(f"Error al cargar perfiles: {e}")
            # Inicializar con estructura de carpetas vacía
            return {"DEFAULT": []}

    def get_profile_by_name(
        self, name: str, folder: Optional[str] = None
    ) -> Tuple[Optional[ConnectionProfile], Optional[str], int]:
        """
        Busca un perfil por nombre en todas las carpetas o en una carpeta específica

        Args:
            name: Nombre del perfil
            folder: Carpeta donde buscar (opcional)

        Returns:
            Una tupla con (perfil, carpeta, índice) o (None, None, -1) si no se encuentra
        """
        folders_to_search = [folder] if folder else self.get_folders()

        for current_folder in folders_to_search:
            profiles = self.get_profiles(current_folder)
            for i, profile_data in enumerate(profiles):
                if profile_data.get("name") == name:
                    return ConnectionProfile.from_dict(profile_data), current_folder, i

        return None, None, -1

    def get_folders(self) -> List[str]:
        """Obtiene la lista de carpetas disponibles"""
        profiles_data = self.get_profiles()
        return list(profiles_data.keys())

    def save_profiles_data(self, profiles_data: Dict[str, List[dict]]) -> bool:
        """
        Guarda los datos de perfiles

        Args:
            profiles_data: Diccionario de carpetas con listas de perfiles

        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            self.settings.setValue("connection_profiles", json.dumps(profiles_data))
            return True
        except Exception as e:
            print(f"Error al guardar perfiles: {e}")
            return False

    def add_profile(self, profile: ConnectionProfile, folder: str = "DEFAULT") -> bool:
        """
        Añade un perfil a una carpeta

        Args:
            profile: Perfil a añadir
            folder: Carpeta donde añadir el perfil

        Returns:
            True si se añadió correctamente, False en caso contrario
        """
        if not profile.is_valid():
            return False

        profiles_data = self.get_profiles()
        if folder not in profiles_data:
            profiles_data[folder] = []

        # Verificar si ya existe un perfil con el mismo nombre en la carpeta
        for existing_profile in profiles_data[folder]:
            if existing_profile.get("name") == profile.name:
                return False

        profiles_data[folder].append(profile.to_dict())
        return self.save_profiles_data(profiles_data)

    def update_profile(
        self, folder: str, index: int, profile: ConnectionProfile
    ) -> bool:
        """
        Actualiza un perfil existente

        Args:
            folder: Carpeta del perfil
            index: Índice del perfil en la carpeta
            profile: Nuevos datos del perfil

        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        if not profile.is_valid():
            return False

        profiles_data = self.get_profiles()
        if folder in profiles_data and 0 <= index < len(profiles_data[folder]):
            profiles_data[folder][index] = profile.to_dict()
            return self.save_profiles_data(profiles_data)
        return False

    def delete_profile(self, folder: str, index: int) -> bool:
        """
        Elimina un perfil

        Args:
            folder: Carpeta del perfil
            index: Índice del perfil en la carpeta

        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        profiles_data = self.get_profiles()
        if folder in profiles_data and 0 <= index < len(profiles_data[folder]):
            del profiles_data[folder][index]
            return self.save_profiles_data(profiles_data)
        return False

    def get_profile_names(self, folder: str = "DEFAULT") -> List[str]:
        """
        Obtiene los nombres de todos los perfiles en una carpeta

        Args:
            folder: Carpeta de perfiles

        Returns:
            Lista de nombres de perfiles
        """
        return [profile.get("name", "") for profile in self.get_profiles(folder)]

    def add_folder(self, folder_name: str) -> bool:
        """
        Añade una nueva carpeta

        Args:
            folder_name: Nombre de la carpeta

        Returns:
            True si se añadió correctamente, False en caso contrario
        """
        if not folder_name:
            return False

        profiles_data = self.get_profiles()
        if folder_name not in profiles_data:
            profiles_data[folder_name] = []
            return self.save_profiles_data(profiles_data)
        return False

    def rename_folder(self, old_name: str, new_name: str) -> bool:
        """
        Renombra una carpeta

        Args:
            old_name: Nombre actual de la carpeta
            new_name: Nuevo nombre para la carpeta

        Returns:
            True si se renombró correctamente, False en caso contrario
        """
        if not new_name or old_name == new_name or old_name == "DEFAULT":
            return False

        profiles_data = self.get_profiles()
        if old_name in profiles_data and new_name not in profiles_data:
            profiles_data[new_name] = profiles_data.pop(old_name)
            return self.save_profiles_data(profiles_data)
        return False

    def delete_folder(self, folder_name: str) -> bool:
        """
        Elimina una carpeta y todos sus perfiles

        Args:
            folder_name: Nombre de la carpeta

        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        if folder_name == "DEFAULT":
            return False  # No permitir eliminar la carpeta por defecto

        profiles_data = self.get_profiles()
        if folder_name in profiles_data:
            del profiles_data[folder_name]
            return self.save_profiles_data(profiles_data)
        return False

    def move_profile(self, source_folder: str, index: int, target_folder: str) -> bool:
        """
        Mueve un perfil de una carpeta a otra

        Args:
            source_folder: Carpeta origen
            index: Índice del perfil en la carpeta origen
            target_folder: Carpeta destino

        Returns:
            True si se movió correctamente, False en caso contrario
        """
        profiles_data = self.get_profiles()
        if (
            source_folder in profiles_data
            and target_folder in profiles_data
            and 0 <= index < len(profiles_data[source_folder])
        ):
            profile = profiles_data[source_folder].pop(index)
            profiles_data[target_folder].append(profile)
            return self.save_profiles_data(profiles_data)
        return False

    def export_profiles(self) -> str:
        """
        Exporta todos los perfiles a JSON

        Returns:
            String JSON con todos los perfiles
        """
        return json.dumps(self.get_profiles(), indent=2)

    def import_profiles(self, json_data: str) -> Tuple[bool, int, List[str]]:
        """
        Importa perfiles desde JSON

        Args:
            json_data: String JSON con perfiles

        Returns:
            Tupla con (éxito, número de perfiles importados, errores)
        """
        errors = []
        try:
            imported_data = json.loads(json_data)

            # Comprobar formato
            if isinstance(imported_data, dict):
                # Formato con carpetas
                imported_folders = imported_data
            elif isinstance(imported_data, list):
                # Lista simple de perfiles
                imported_folders = {"DEFAULT": imported_data}
            else:
                return False, 0, ["Formato de importación no válido"]

            # Validar perfiles
            total_imported = 0
            current_profiles = self.get_profiles()

            for folder, profiles in imported_folders.items():
                if not isinstance(profiles, list):
                    errors.append(f"La carpeta '{folder}' no contiene una lista válida")
                    continue

                if folder not in current_profiles:
                    current_profiles[folder] = []

                for profile_data in profiles:
                    if not isinstance(profile_data, dict) or "name" not in profile_data:
                        errors.append(f"Perfil no válido en carpeta '{folder}'")
                        continue

                    # Validar perfil
                    profile = ConnectionProfile.from_dict(profile_data)
                    if not profile.is_valid():
                        errors.append(f"Perfil '{profile.name}' no válido")
                        continue

                    # Añadir perfil
                    current_profiles[folder].append(profile.to_dict())
                    total_imported += 1

            # Guardar perfiles
            if total_imported > 0:
                self.save_profiles_data(current_profiles)
                return True, total_imported, errors
            else:
                return False, 0, errors if errors else ["No se importaron perfiles"]

        except json.JSONDecodeError:
            return False, 0, ["JSON no válido"]
        except Exception as e:
            return False, 0, [f"Error al importar: {str(e)}"]
