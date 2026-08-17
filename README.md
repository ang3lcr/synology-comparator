# Synology File Comparator

Una aplicación de escritorio en Python/PySide6 para comparar una carpeta local de Windows/Linux contra una carpeta en un NAS Synology, utilizando las APIs oficiales de Synology.

## Requisitos

- Python 3.12+
- Dependencias (ver `requirements.txt`)

## Instalación

1. Clona el repositorio o descarga el código.
2. Crea un entorno virtual e instala las dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Uso

1. Ejecuta la aplicación:
   ```bash
   python main.py
   ```
2. Haz clic en **Conectar a NAS**.
3. Ingresa tu QuickConnect ID o Dirección IP del NAS, junto con tu Usuario y Contraseña.
4. Selecciona una carpeta local utilizando el botón **Examinar**.
5. Escribe la ruta de la carpeta remota del NAS (ej. `/Documentos/Proyecto2026`).
6. Haz clic en **COMPARAR ARCHIVOS**.
7. Los resultados aparecerán en la tabla y se mostrará un resumen de archivos coincidentes, faltantes, diferentes y aquellos que solo existen en el NAS.

## Fases de Desarrollo

* **Fase 1**: (Completada) Interfaz principal, conexión mediante `synology-api`, escaneo asíncrono y tabla de resultados.
* **Fase 2**: (Pendiente) Optimización con SQLite, lotes, exportación a CSV/Excel.
* **Fase 3**: (Pendiente) Verificación MD5 y subida de archivos faltantes.
