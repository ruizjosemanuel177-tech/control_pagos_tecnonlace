from flask import Flask, render_template, request, redirect, url_for, send_file, session
from flask_session import Session
import sqlite3
from datetime import datetime
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
import os
import psycopg2
import urllib.parse as up

app = Flask(__name__)
app.secret_key = "tecnoenlace_secret"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# --- Detectar si estamos en Render (usa PostgreSQL) o local (usa SQLite) ---
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    up.uses_netloc.append("postgres")
    url = up.urlparse(DATABASE_URL)
    def get_db():
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        return conn
else:
    def get_db():
        conn = sqlite3.connect("usuarios.db")
        conn.row_factory = sqlite3.Row
        return conn

# --- Usuarios por defecto ---
usuarios_predeterminados = [
    "Edgar Arevalo","Adonay Ledezma","Luis Angel Agredo","Andres Collazos","Asprosi",
    "Yazmin Lopez","Moises Lopez","Jarvy Ledezma","Yaneth Ordoñez","Daniela Muñoz",
    "Jose Luis Cruz","Oscar Ordoñez","Aleida Chicangana","Jhonatan Salazar","Xiomara Dorado",
    "Isabela Ausecha","Angel Cordoba","Deyanira Lopez","Wilmer Diaz","Jose Wifar Ordoñez",
    "Brayan Felipe Alvarez","Jaiver Ordoñez","Ximena Hernandez","Eriberto Delgado","Quenier Campo",
    "Yolanda Garzon","Mariela Avendaño","Ivan Perez","Benicio Paz","Leni Campo",
    "Gustavo Martinez","Arnovi Paz","Eider Alexander Dorado","Andres Muñoz","Lamet Quijano",
    "Deyanira Ausecha","Yohan Ledezma","Anderson Paz","Eliana Mosquera"
]

# --- Inicializar base de datos (solo si SQLite) ---
def init_db():
    if not DATABASE_URL:
        conn = sqlite3.connect("usuarios.db")
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            activo INTEGER
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            monto REAL,
            fecha TEXT
        )""")
        for u in usuarios_predeterminados:
            cur.execute("INSERT OR IGNORE INTO usuarios (nombre, activo) VALUES (?,?)", (u,1))
        conn.commit()
        conn.close()

init_db()

# -------- LOGIN --------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        usuario = request.form["usuario"]
        password = request.form["password"]
        if usuario=="TECNOENLACE" and password=="TECNOENLACE2025":
            session["logged_in"] = True
            return redirect(url_for("dashboard", section="usuarios"))
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------- DASHBOARD --------
@app.route("/dashboard/<section>", methods=["GET","POST"])
def dashboard(section):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    # Registrar usuario
    if section=="registrar_usuario" and request.method=="POST":
        nombre = request.form["nombre"]
        if DATABASE_URL:
            cur.execute("INSERT INTO usuarios (nombre, activo) VALUES (%s, %s) ON CONFLICT (nombre) DO NOTHING", (nombre,1))
        else:
            cur.execute("INSERT OR IGNORE INTO usuarios (nombre, activo) VALUES (?,?)",(nombre,1))
        conn.commit()
        return redirect(url_for("dashboard", section="usuarios"))

    # Registrar pago
    if section=="registrar_pago" and request.method=="POST":
        usuario = request.form["usuario"]
        monto = float(request.form["monto"])
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if DATABASE_URL:
            cur.execute("INSERT INTO pagos (usuario, monto, fecha) VALUES (%s,%s,%s)",(usuario,monto,fecha))
            cur.execute("UPDATE usuarios SET activo=1 WHERE nombre=%s",(usuario,))
        else:
            cur.execute("INSERT INTO pagos (usuario, monto, fecha) VALUES (?,?,?)",(usuario,monto,fecha))
            cur.execute("UPDATE usuarios SET activo=1 WHERE nombre=?",(usuario,))
        conn.commit()
        return redirect(url_for("dashboard", section="pagos"))

    # --- BÚSQUEDA DE USUARIOS ---
    search_query = request.args.get("buscar", "").strip()
    if search_query:
        if DATABASE_URL:
            cur.execute("SELECT * FROM usuarios WHERE nombre ILIKE %s", (f"%{search_query}%",))
        else:
            cur.execute("SELECT * FROM usuarios WHERE nombre LIKE ?", (f"%{search_query}%",))
    else:
        cur.execute("SELECT * FROM usuarios")
    usuarios = cur.fetchall()

    # Consultas generales
    cur.execute("SELECT * FROM pagos")
    pagos = cur.fetchall()

    if DATABASE_URL:
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo=1")
        activos = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo=0")
        corte = cur.fetchone()[0]
    else:
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo=1")
        activos = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo=0")
        corte = cur.fetchone()[0]

    estadisticas = {"activos":activos,"corte":corte}
    conn.close()

    return render_template("dashboard.html", section=section, usuarios=usuarios, pagos=pagos, estadisticas=estadisticas, search_query=search_query)

# -------- EXPORTAR --------
@app.route("/exportar/<tipo>")
def exportar(tipo):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pagos")
    pagos = cur.fetchall()
    conn.close()

    if tipo=="excel":
        df = pd.DataFrame(pagos, columns=['id','usuario','monto','fecha'])
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return send_file(output, download_name="pagos.xlsx", as_attachment=True)
    elif tipo=="pdf":
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=(600,800))
        y = 750
        c.setFont("Helvetica-Bold",14)
        c.drawString(50, y, "Reporte de Pagos TECNOENLACE")
        y-=30
        c.setFont("Helvetica",12)
        for p in pagos:
            c.drawString(50,y,str(p[1]))  # usuario
            c.drawString(200,y,str(p[2])) # monto
            c.drawString(300,y,str(p[3])) # fecha
            y-=20
            if y<50:
                c.showPage()
                y=750
        c.save()
        output.seek(0)
        return send_file(output, download_name="pagos.pdf", as_attachment=True)
    return "Formato no válido",400

# -------- EDITAR / BORRAR / ACTIVAR-DESACTIVAR --------
@app.route("/editar_usuario/<int:id>", methods=["GET","POST"])
def editar_usuario(id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    if request.method=="POST":
        nombre = request.form["nombre"]
        if DATABASE_URL:
            cur.execute("UPDATE usuarios SET nombre=%s WHERE id=%s",(nombre,id))
        else:
            cur.execute("UPDATE usuarios SET nombre=? WHERE id=?",(nombre,id))
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard", section="usuarios"))
    if DATABASE_URL:
        cur.execute("SELECT * FROM usuarios WHERE id=%s",(id,))
    else:
        cur.execute("SELECT * FROM usuarios WHERE id=?",(id,))
    usuario = cur.fetchone()
    conn.close()
    return render_template("editar_usuario.html", usuario=usuario)

@app.route("/borrar_usuario/<int:id>")
def borrar_usuario(id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    if DATABASE_URL:
        cur.execute("DELETE FROM usuarios WHERE id=%s",(id,))
    else:
        cur.execute("DELETE FROM usuarios WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", section="usuarios"))

@app.route("/activar_usuario/<int:id>")
def activar_usuario(id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    if DATABASE_URL:
        cur.execute("UPDATE usuarios SET activo=1 WHERE id=%s",(id,))
    else:
        cur.execute("UPDATE usuarios SET activo=1 WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", section="usuarios"))

@app.route("/desactivar_usuario/<int:id>")
def desactivar_usuario(id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    if DATABASE_URL:
        cur.execute("UPDATE usuarios SET activo=0 WHERE id=%s",(id,))
    else:
        cur.execute("UPDATE usuarios SET activo=0 WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", section="usuarios"))

@app.route("/editar_pago/<int:id>", methods=["GET","POST"])
def editar_pago(id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    if request.method=="POST":
        usuario = request.form["usuario"]
        monto = float(request.form["monto"])
        if DATABASE_URL:
            cur.execute("UPDATE pagos SET usuario=%s, monto=%s WHERE id=%s",(usuario,monto,id))
        else:
            cur.execute("UPDATE pagos SET usuario=?, monto=? WHERE id=?",(usuario,monto,id))
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard", section="pagos"))
    if DATABASE_URL:
        cur.execute("SELECT * FROM pagos WHERE id=%s",(id,))
        pago = cur.fetchone()
        cur.execute("SELECT nombre FROM usuarios")
        usuarios = cur.fetchall()
    else:
        cur.execute("SELECT * FROM pagos WHERE id=?",(id,))
        pago = cur.fetchone()
        cur.execute("SELECT nombre FROM usuarios")
        usuarios = cur.fetchall()
    conn.close()
    return render_template("editar_pago.html", pago=pago, usuarios=usuarios)

@app.route("/borrar_pago/<int:id>")
def borrar_pago(id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    if DATABASE_URL:
        cur.execute("DELETE FROM pagos WHERE id=%s",(id,))
    else:
        cur.execute("DELETE FROM pagos WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", section="pagos"))

# -------- EJECUTAR APLICACIÓN --------
if __name__=="__main__":
    port = int(os.environ.get("PORT",5055))
    app.run(debug=True, host="0.0.0.0", port=port)