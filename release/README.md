# Kanban Docker Quick Install

Este paquete permite instalar Kanban en segundos usando Docker y la imagen oficial de GHCR.

## Pasos rápidos

1. Descarga y descomprime el release:
   ```bash
   tar -xzf kanban-release.tar.gz
   cd kanban-release
   ```
2. Ejecuta el instalador interactivo:
   ```bash
   bash install.sh
   ```
3. Sigue las instrucciones en pantalla para definir SECRET_KEY, puertos y credenciales admin.
4. Accede a la app en http://localhost:8000 (o el puerto que elegiste).

## Archivos incluidos
- `.env.example` — plantilla de configuración
- `docker-compose.release.yml` — stack de Docker listo para producción
- `install.sh` — script interactivo de instalación
- `upgrade.sh` — script de actualización automática
- `README.md` — este instructivo

## Requisitos
- Docker y Docker Compose instalados
- (Opcional) GitHub token si la imagen es privada

## Actualización (upgrade)

Para actualizar a una nueva versión:

1. Descarga y descomprime el nuevo kanban-release.tar.gz
2. Copia tu `.env` anterior (o usa el que ya tienes)
3. Ejecuta:
   ```bash
   bash upgrade.sh
   ```
   El script detecta si hay instalación previa y, si no, ejecuta install.sh automáticamente.

## Notas
- El script genera un SECRET_KEY seguro si no lo defines.
- Puedes cambiar cualquier variable en `.env` después de la instalación.
