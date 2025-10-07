
Control de Pagos TECNOENLACE - Versión móvil (TailwindCSS)

Contenido del paquete:
 - app.py                 -> servidor Flask
 - templates/             -> páginas HTML con Tailwind (CDN)
 - static/css/mobile.css  -> ajustes mínimos
 - pagos.db               -> (se crea automáticamente al ejecutar)

Credenciales (por defecto):
 - Usuario: TECNOENLACE
 - Clave: TECNOENLACE2025

Requisitos:
 - Python 3.x
 - pip install flask openpyxl

¿Cómo ejecutar?
1. Descomprime este paquete.
2. Abre CMD en la carpeta del proyecto.
3. Instala dependencias:
   python -m pip install flask openpyxl
4. Ejecuta:
   python app.py
5. Abre en tu navegador (PC): http://127.0.0.1:5000
   O desde tu celular (misma red): http://<IP-de-tu-PC>:5000
