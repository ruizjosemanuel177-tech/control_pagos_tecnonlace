from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# =========================
# 🔹 CONEXIÓN A BASE DE DATOS
# =========================
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# 🔹 INICIALIZAR BASE DE DATOS
# =========================
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            estado TEXT DEFAULT 'Activo'
        )
    """)
    conn.commit()
    conn.close()


# =========================
# 🔹 REPARAR BASE DE DATOS (si falta columna)
# =========================
def fix_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(clientes)")
    cols = [c[1] for c in cur.fetchall()]
    if "estado" not in cols:
        print("Añadiendo columna 'estado' a la tabla clientes...")
        cur.execute("ALTER TABLE clientes ADD COLUMN estado TEXT DEFAULT 'Activo'")
        conn.commit()
        print("✅ Columna 'estado' añadida correctamente.")
    else:
        print("✅ La columna 'estado' ya existe.")
    conn.close()


# =========================
# 🔹 RUTAS
# =========================
@app.route("/")
def index():
    return redirect(url_for("clientes"))


@app.route("/clientes")
def clientes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clientes")
    data = cur.fetchall()
    conn.close()
    return render_template("clientes.html", clientes=data)


@app.route("/agregar", methods=["POST"])
def agregar():
    nombre = request.form["nombre"]
    telefono = request.form["telefono"]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO clientes (nombre, telefono, estado) VALUES (?, ?, 'Activo')", (nombre, telefono))
    conn.commit()
    conn.close()
    return redirect(url_for("clientes"))


@app.route("/suspender/<int:id>")
def suspender(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE clientes SET estado='Cortado' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("clientes"))


@app.route("/activar/<int:id>")
def activar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE clientes SET estado='Activo' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("clientes"))


@app.route("/dashboard")
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as total FROM clientes")
    total = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as activos FROM clientes WHERE estado='Activo'")
    activos = cur.fetchone()["activos"]

    cur.execute("SELECT COUNT(*) as cortados FROM clientes WHERE estado='Cortado'")
    cortados = cur.fetchone()["cortados"]

    conn.close()
    return render_template("dashboard.html", total=total, activos=activos, cortados=cortados)


# =========================
# 🔹 INICIO DE APLICACIÓN
# =========================
if __name__ == "__main__":
    init_db()   # Crea la tabla si no existe
    fix_db()    # Corrige estructura si falta columna
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


