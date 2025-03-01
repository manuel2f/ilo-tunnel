import unittest
import tempfile
import os
import json
import sys
import shutil
from pathlib import Path

# Añadir directorio principal al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar después de modificar el path
from ilo_tunnel.config import Config

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Crear un directorio temporal para las pruebas
        self.test_dir = tempfile.mkdtemp()
        self.original_config_dir = os.environ.get('ILO_TUNNEL_CONFIG_DIR', '')
        os.environ['ILO_TUNNEL_CONFIG_DIR'] = self.test_dir
        
    def tearDown(self):
        # Limpiar después de las pruebas
        shutil.rmtree(self.test_dir)
        if self.original_config_dir:
            os.environ['ILO_TUNNEL_CONFIG_DIR'] = self.original_config_dir
        else:
            os.environ.pop('ILO_TUNNEL_CONFIG_DIR', None)
    
    def test_config_get_set(self):
        config = Config()
        config.set('test_key', 'test_value')
        self.assertEqual(config.get('test_key'), 'test_value')
        self.assertEqual(config.get('non_existent'), None)
        self.assertEqual(config.get('non_existent', 'default'), 'default')

if __name__ == '__main__':
    unittest.main()
