# TECNOENLACE - Aplicación de gestión de usuarios y pagos

## Qué incluye
- Backend: Flask (app.py)
- Frontend: Plantilla HTML + JS estático (templates/index.html, static/)
- Base de datos: SQLite (tecnoenlace.db se crea al iniciar)
- Exportes: Excel y PDF (endpoints /export/...)
- Dockerfile y docker-compose para desplegar localmente

## Credenciales por defecto
- Usuario: TECNOENLACE
- Contraseña: TECNOENLACE2025

## Ejecutar localmente
1. Crear venv e instalar dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\\Scripts\\activate    # Windows
   pip install -r requirements.txt
   ```
2. Ejecutar:
   ```bash
   python app.py
   ```
3. Abrir: http://localhost:5000/
