import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# Crear tabla de clientes
cur.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    direccion TEXT,
    telefono TEXT,
    correo TEXT
)
""")

# Crear tabla de pagos
cur.execute("""
CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    monto REAL NOT NULL,
    fecha TEXT NOT NULL,
    metodo_pago TEXT,
    estado TEXT DEFAULT 'Normal',
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
)
""")

conn.commit()
conn.close()

print("✅ Base de datos creada correctamente (database.db)")
