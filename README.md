# ILO Tunnel Manager

Una aplicación multiplataforma con interfaz gráfica para gestionar túneles SSH para interfaces HP ProLiant ILO & Huawei.

## Características

- Interfaz gráfica fácil de usar
- Soporte para múltiples puertos de túnel
- Guardado y carga de configuraciones
- Soporte multiplataforma (Windows, macOS, Linux)
- Apertura automática de navegador web

## Instalación

### Desde código fuente

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/ilo-tunnel.git
cd ilo-tunnel

# Instalar dependencias
pip install -r requirements.txt

# Instalar el paquete
pip install -e .
```

### Usando binarios precompilados

Descarga los binarios desde la sección de Releases.

## Uso

```bash
# Ejecutar la aplicación desde línea de comandos
ilo-tunnel

# O ejecuta el binario descargado
```

## Desarrollo

### Estructura del proyecto

```
ilo-tunnel/
├── ilo_tunnel/         # Paquete principal
├── scripts/            # Scripts de utilidad
├── tests/              # Pruebas unitarias
└── docs/               # Documentación
```

### Construir el proyecto

```bash
./scripts/build.sh
```

## Licencia

MIT
