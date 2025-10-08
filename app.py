from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3, os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "TECNOENLACE2025"

DB_PATH = "database.db"

# ---------------------------------------------------
# FUNCIONES BASE DE DATOS
# ---------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        estado TEXT DEFAULT 'Cortado'
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pagos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        monto REAL,
        fecha TEXT,
        mes TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )
    """)
    conn.commit()
    conn.close()

    # Usuarios iniciales
    clientes_iniciales = [
        "Edgar Arevalo","Adonay Ledezma","Luis Angel Agredo","Andres Collazos","Asprosi",
        "Yazmin Lopez","Moises Lopez","Jarvy Ledezma","Yaneth Ordoñez","Daniela Muñoz",
        "Jose Luis Cruz","Oscar Ordoñez","Aleida Chicangana","Jhonatan Salazar","Xiomara Dorado",
        "Isabela Ausecha","Angel Cordoba","Deyanira Lopez","Wilmer Diaz","Jose Wifar Ordoñez",
        "Brayan Felipe Alvarez","Jaiver Ordoñez","Ximena Hernandez","Eriberto Delgado","Quenier Campo",
        "Yolanda Garzon","Mariela Avendaño","Ivan Perez","Benicio Paz","Leni Campo",
        "Gustavo Martinez","Arnovi Paz","Eider Alexander Dorado","Andres Muñoz","Lamet Quijano",
        "Deyanira Ausecha","Yohan Ledezma","Anderson Paz","Eliana Mosquera"
    ]
    conn = get_db()
    cur = conn.cursor()
    for nombre in clientes_iniciales:
        cur.execute("INSERT OR IGNORE INTO clientes (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        contrasena = request.form["contrasena"]
        if usuario == "TECNOENLACE" and contrasena == "TECNOENLACE2025":
            session["usuario"] = usuario
            return redirect(url_for("dashboard"))
        else:
            flash("Usuario o contraseña incorrectos", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM clientes")
    total_clientes = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as activos FROM clientes WHERE estado='Activo'")
    activos = cur.fetchone()["activos"]
    cur.execute("SELECT COUNT(*) as cortados FROM clientes WHERE estado='Cortado'")
    cortados = cur.fetchone()["cortados"]
    conn.close()
    return render_template("dashboard.html", total=total_clientes, activos=activos, cortados=cortados)

# ---------------------------------------------------
# CLIENTES
# ---------------------------------------------------
@app.route("/clientes")
def clientes():
    if "usuario" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clientes")
    clientes = cur.fetchall()
    conn.close()
    return render_template("clientes.html", clientes=clientes)

@app.route("/activar/<int:id>")
def activar(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE clientes SET estado='Activo' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("clientes"))

@app.route("/cortar/<int:id>")
def cortar(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE clientes SET estado='Cortado' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("clientes"))

@app.route("/borrar_cliente/<int:id>")
def borrar_cliente(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM clientes WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("clientes"))

# ---------------------------------------------------
# PAGOS
# ---------------------------------------------------
@app.route("/pagos")
def pagos():
    if "usuario" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    SELECT pagos.id, clientes.nombre, pagos.monto, pagos.fecha, pagos.mes
    FROM pagos
    JOIN clientes ON clientes.id = pagos.cliente_id
    """)
    pagos = cur.fetchall()
    conn.close()
    return render_template("pagos.html", pagos=pagos)

@app.route("/nuevo_pago", methods=["POST"])
def nuevo_pago():
    cliente_id = request.form["cliente_id"]
    monto = request.form["monto"]
    fecha = request.form["fecha"]
    mes = request.form["mes"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO pagos (cliente_id, monto, fecha, mes) VALUES (?, ?, ?, ?)", (cliente_id, monto, fecha, mes))
    cur.execute("UPDATE clientes SET estado='Activo' WHERE id=?", (cliente_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("pagos"))

@app.route("/borrar_pago/<int:id>")
def borrar_pago(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM pagos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("pagos"))

# ---------------------------------------------------
# EXPORTAR
# ---------------------------------------------------
@app.route("/exportar_excel")
def exportar_excel():
    conn = get_db()
    df = pd.read_sql_query("""
        SELECT clientes.nombre AS Cliente, pagos.monto AS Monto, pagos.fecha AS Fecha, pagos.mes AS Mes
        FROM pagos
        JOIN clientes ON clientes.id = pagos.cliente_id
    """, conn)
    path = "reporte_pagos.xlsx"
    df.to_excel(path, index=False)
    conn.close()
    return send_file(path, as_attachment=True)

@app.route("/exportar_pdf")
def exportar_pdf():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT clientes.nombre, pagos.monto, pagos.fecha, pagos.mes
        FROM pagos
        JOIN clientes ON clientes.id = pagos.cliente_id
    """)
    rows = cur.fetchall()
    conn.close()

    pdf_path = "reporte_pagos.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    y = 750
    c.drawString(50, y, "Reporte de Pagos - TECNOENLACE")
    y -= 40
    for r in rows:
        c.drawString(50, y, f"{r['nombre']} | ${r['monto']} | {r['fecha']} | {r['mes']}")
        y -= 20
    c.save()
    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render asigna el puerto automáticamente
    app.run(host="0.0.0.0", port=port)



