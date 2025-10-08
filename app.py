from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "tecnoenlace_secret"

# ===========================
#  CONEXIÓN Y BASE DE DATOS
# ===========================
DB_NAME = "tecnoenlace.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        # Crear tabla clientes si no existe
        cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            estado TEXT DEFAULT 'Corte'
        )
        """)
        # Crear tabla pagos si no existe
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
        # Insertar lista inicial de clientes si la tabla está vacía
        cur.execute("SELECT COUNT(*) FROM clientes")
        if cur.fetchone()[0] == 0:
            clientes = [
                'Edgar Arevalo','Adonay Ledezma','Luis Angel Agredo','Andres Collazos','Asprosi','Yazmin Lopez',
                'Moises Lopez','Jarvy Ledezma','Yaneth Ordoñez','Daniela Muñoz','Jose Luis Cruz','Oscar Ordoñez',
                'Aleida Chicangana','Jhonatan Salazar','Xiomara Dorado','Isabela Ausecha','Angel Cordoba',
                'Deyanira Lopez','Wilmer Diaz','Jose Wifar Ordoñez','Brayan Felipe Alvarez','Jaiver Ordoñez',
                'Ximena Hernandez','Eriberto Delgado','Quenier Campo','Yolanda Garzon','Mariela Avendaño',
                'Ivan Perez','Benicio Paz','Leni Campo','Gustavo Martinez','Arnovi Paz','Eider Alexander Dorado',
                'Andres Muñoz','Lamet Quijano','Deyanira Ausecha','Yohan Ledezma','Anderson Paz','Eliana Mosquera'
            ]
            for nombre in clientes:
                cur.execute("INSERT INTO clientes (nombre, estado) VALUES (?, 'Corte')", (nombre,))
        conn.commit()

# ===========================
#       LOGIN
# ===========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]
        if user == "TECNOENLACE" and password == "TECNOENLACE2025":
            session["user"] = user
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Credenciales incorrectas")
    return render_template("login.html")

# ===========================
#     DASHBOARD PRINCIPAL
# ===========================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM clientes")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM clientes WHERE estado='Activo'")
        activos = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM clientes WHERE estado='Corte'")
        cortados = cur.fetchone()[0]
    return render_template("dashboard.html", total=total, activos=activos, cortados=cortados)

# ===========================
#     CLIENTES CRUD
# ===========================
@app.route("/clientes")
def clientes():
    if "user" not in session:
        return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM clientes")
        lista = cur.fetchall()
    return render_template("clientes.html", clientes=lista)

@app.route("/agregar", methods=["POST"])
def agregar():
    nombre = request.form["nombre"]
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO clientes (nombre, estado) VALUES (?, 'Corte')", (nombre,))
        conn.commit()
    return redirect(url_for("clientes"))

@app.route("/eliminar/<int:id>")
def eliminar(id):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM clientes WHERE id=?", (id,))
        conn.commit()
    return redirect(url_for("clientes"))

@app.route("/activar/<int:id>")
def activar(id):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE clientes SET estado='Activo' WHERE id=?", (id,))
        conn.commit()
    return redirect(url_for("clientes"))

@app.route("/cortar/<int:id>")
def cortar(id):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE clientes SET estado='Corte' WHERE id=?", (id,))
        conn.commit()
    return redirect(url_for("clientes"))

# ===========================
#     PAGOS (ARREGLADO)
# ===========================
@app.route("/pagos")
def pagos():
    if "user" not in session:
        return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT pagos.id, clientes.nombre, pagos.monto, pagos.fecha, pagos.mes
            FROM pagos
            JOIN clientes ON pagos.cliente_id = clientes.id
        """)
        lista_pagos = cur.fetchall()
    return render_template("pagos.html", pagos=lista_pagos)

# Registrar pago y activar automáticamente el servicio
@app.route("/registrar_pago", methods=["POST"])
def registrar_pago():
    cliente_id = request.form["cliente_id"]
    monto = request.form["monto"]
    fecha = request.form["fecha"]
    mes = request.form["mes"]
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO pagos (cliente_id, monto, fecha, mes) VALUES (?, ?, ?, ?)", (cliente_id, monto, fecha, mes))
        cur.execute("UPDATE clientes SET estado='Activo' WHERE id=?", (cliente_id,))
        conn.commit()
    return redirect(url_for("pagos"))

# ===========================
#   EXPORTAR DATOS
# ===========================
@app.route("/exportar_excel")
def exportar_excel():
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query("SELECT * FROM pagos", conn)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="pagos.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/exportar_pdf")
def exportar_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "Reporte de Pagos - TECNOENLACE")
    y = 720
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM pagos")
        pagos = cur.fetchall()
    for p in pagos:
        c.drawString(100, y, f"ID: {p[0]} | Cliente: {p[1]} | Monto: {p[2]} | Fecha: {p[3]} | Mes: {p[4]}")
        y -= 20
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="pagos.pdf", mimetype="application/pdf")

# ===========================
#   CERRAR SESIÓN
# ===========================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ===========================
#     INICIALIZAR APP
# ===========================
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0")



