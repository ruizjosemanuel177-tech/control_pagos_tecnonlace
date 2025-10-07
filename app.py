from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import sqlite3, os
from datetime import datetime

# --- Configuración ---
APP_SECRET = "tecnonlace_secret_2025"
DB_PATH = os.path.join(os.path.dirname(__file__), "pagos.db")
USERNAME = "TECNOENLACE"
PASSWORD = "TECNOENLACE2025"

# --- App Flask ---
app = Flask(__name__)
app.secret_key = APP_SECRET

# --- Base de datos ---
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            estado_servicio TEXT DEFAULT 'Normal'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            monto REAL NOT NULL,
            fecha_pago TEXT NOT NULL,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    """)
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# --- Sesión ---
def logged_in():
    return session.get("logged_in", False)

# --- Rutas ---
@app.route("/login", methods=["GET","POST"])
def login():
    if logged_in():
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        user = request.form.get("username","").strip()
        pwd = request.form.get("password","").strip()
        if user == USERNAME and pwd == PASSWORD:
            session["logged_in"] = True
            session["user"] = user
            return redirect(url_for("dashboard"))
        else:
            error = "Usuario o clave incorrectos."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))

@app.route("/")
def index():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    if not logged_in(): return redirect(url_for("login"))
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT COUNT(*) as c FROM clientes"); total_clientes = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM pagos WHERE date(fecha_pago) >= date('now','-30 day')"); pagos_30 = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM clientes WHERE lower(estado_servicio) = 'corte'"); en_corte = cur.fetchone()["c"]
    return render_template("dashboard.html", total_clientes=total_clientes, pagos_30=pagos_30, en_corte=en_corte)

@app.route("/clientes")
def clientes():
    if not logged_in(): return redirect(url_for("login"))
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT * FROM clientes ORDER BY id DESC"); clientes_list = cur.fetchall()
    return render_template("clientes.html", clientes=clientes_list)

@app.route("/clientes/add", methods=["POST"])
def clientes_add():
    if not logged_in(): return redirect(url_for("login"))
    nombre = request.form.get("nombre","").strip()
    telefono = request.form.get("telefono","").strip()
    if not nombre:
        flash("El nombre es obligatorio.", "danger")
        return redirect(url_for("clientes"))
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO clientes (nombre, telefono) VALUES (?,?)", (nombre, telefono))
    db.commit()
    flash("Cliente agregado.", "success")
    return redirect(url_for("clientes"))

@app.route("/suspender/<int:cliente_id>")
def suspender_servicio(cliente_id):
    if not logged_in(): return redirect(url_for("login"))
    db = get_db(); cur = db.cursor()
    cur.execute("UPDATE clientes SET estado_servicio='Corte' WHERE id=?", (cliente_id,))
    db.commit()
    flash("Servicio suspendido.", "warning")
    return redirect(url_for("clientes"))

@app.route("/pagos")
def pagos():
    if not logged_in(): return redirect(url_for("login"))
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT p.*, c.nombre as cliente_nombre FROM pagos p JOIN clientes c ON p.cliente_id = c.id ORDER BY p.id DESC")
    pagos_list = cur.fetchall()
    cur.execute("SELECT id,nombre FROM clientes ORDER BY nombre"); clientes_list = cur.fetchall()
    return render_template("pagos.html", pagos=pagos_list, clientes=clientes_list)

@app.route("/pagos/add", methods=["POST"])
def pagos_add():
    if not logged_in(): return redirect(url_for("login"))
    try: cliente_id = int(request.form.get("cliente_id"))
    except: flash("Cliente inválido.", "danger"); return redirect(url_for("pagos"))
    monto = request.form.get("monto","").strip(); fecha = request.form.get("fecha","").strip()
    if not monto or not fecha: flash("Monto y fecha son obligatorios.", "danger"); return redirect(url_for("pagos"))
    try: monto_f = float(monto)
    except: flash("Monto inválido.", "danger"); return redirect(url_for("pagos"))
    try: fecha_dt = datetime.strptime(fecha, "%Y-%m-%d"); fecha_str = fecha_dt.strftime("%Y-%m-%d")
    except: flash("Formato de fecha inválido. Use AAAA-MM-DD.", "danger"); return redirect(url_for("pagos"))
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO pagos (cliente_id,monto,fecha_pago) VALUES (?,?,?)", (cliente_id, monto_f, fecha_str))
    db.commit(); flash("Pago registrado.", "success")
    return redirect(url_for("pagos"))

# --- Ejecutar ---
if __name__ == "__main__":
    init_db()  # CREA TABLAS SI NO EXISTEN
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
