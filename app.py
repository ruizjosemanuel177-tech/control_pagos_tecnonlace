
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, g
import sqlite3, os, io
from datetime import datetime
from openpyxl import Workbook

APP_SECRET = "tecnonlace_secret_2025"
DB_PATH = os.path.join(os.path.dirname(__file__), "pagos.db")
USERNAME = "TECNOENLACE"
PASSWORD = "TECNOENLACE2025"

app = Flask(__name__)
app.secret_key = APP_SECRET

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, direccion TEXT, telefono TEXT, correo TEXT, estado_servicio TEXT DEFAULT 'Normal')")
    cur.execute("CREATE TABLE IF NOT EXISTS pagos (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER NOT NULL, monto REAL NOT NULL, fecha_pago TEXT NOT NULL, metodo_pago TEXT, mes_correspondiente TEXT, observaciones TEXT, FOREIGN KEY(cliente_id) REFERENCES clientes(id))")
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def logged_in():
    return session.get("logged_in", False)

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
    cur.execute("SELECT * FROM clientes ORDER BY id DESC"); rows = cur.fetchall()
    return render_template("clientes.html", clientes=rows)

@app.route("/clientes/add", methods=["POST"])
def clientes_add():
    if not logged_in(): return redirect(url_for("login"))
    nombre = request.form.get("nombre","").strip()
    direccion = request.form.get("direccion","").strip()
    telefono = request.form.get("telefono","").strip()
    correo = request.form.get("correo","").strip()
    estado = request.form.get("estado","Normal").strip()
    if not nombre:
        flash("El nombre es obligatorio.", "danger"); return redirect(url_for("clientes"))
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO clientes (nombre,direccion,telefono,correo,estado_servicio) VALUES (?,?,?,?,?)", (nombre,direccion,telefono,correo,estado))
    db.commit(); flash("Cliente agregado.", "success"); return redirect(url_for("clientes"))

@app.route("/clientes/edit/<int:cliente_id>", methods=["GET","POST"])
def clientes_edit(cliente_id):
    if not logged_in(): return redirect(url_for("login"))
    db = get_db(); cur = db.cursor()
    if request.method == "POST":
        nombre = request.form.get("nombre","").strip(); direccion = request.form.get("direccion","").strip()
        telefono = request.form.get("telefono","").strip(); correo = request.form.get("correo","").strip(); estado = request.form.get("estado","Normal").strip()
        if not nombre: flash("El nombre es obligatorio.", "danger"); return redirect(url_for("clientes_edit", cliente_id=cliente_id))
        cur.execute("UPDATE clientes SET nombre=?,direccion=?,telefono=?,correo=?,estado_servicio=? WHERE id=?", (nombre,direccion,telefono,correo,estado,cliente_id))
        db.commit(); flash("Cliente actualizado.", "success"); return redirect(url_for("clientes"))
    cur.execute("SELECT * FROM clientes WHERE id=?", (cliente_id,)); cliente = cur.fetchone()
    if not cliente: flash("Cliente no encontrado.", "warning"); return redirect(url_for("clientes"))
    return render_template("clientes_edit.html", cliente=cliente)

@app.route("/pagos")
def pagos():
    if not logged_in(): return redirect(url_for("login"))
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT p.*, c.nombre as cliente_nombre FROM pagos p JOIN clientes c ON p.cliente_id = c.id ORDER BY p.id DESC")
    rows = cur.fetchall()
    cur.execute("SELECT id,nombre FROM clientes ORDER BY nombre"); clientes_list = cur.fetchall()
    return render_template("pagos.html", pagos=rows, clientes=clientes_list)

@app.route("/pagos/add", methods=["POST"])
def pagos_add():
    if not logged_in(): return redirect(url_for("login"))
    try: cliente_id = int(request.form.get("cliente_id"))
    except: flash("Cliente inválido.", "danger"); return redirect(url_for("pagos"))
    monto = request.form.get("monto","").strip(); fecha = request.form.get("fecha","").strip(); metodo = request.form.get("metodo","").strip()
    mes = request.form.get("mes","").strip(); obs = request.form.get("observaciones","").strip()
    if not monto or not fecha: flash("Monto y fecha son obligatorios.", "danger"); return redirect(url_for("pagos"))
    try: monto_f = float(monto)
    except: flash("Monto inválido.", "danger"); return redirect(url_for("pagos"))
    try: fecha_dt = datetime.strptime(fecha, "%Y-%m-%d"); fecha_str = fecha_dt.strftime("%Y-%m-%d")
    except: flash("Formato de fecha inválido. Use AAAA-MM-DD.", "danger"); return redirect(url_for("pagos"))
    if not mes: mes = fecha_dt.strftime("%B %Y")
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO pagos (cliente_id,monto,fecha_pago,metodo_pago,mes_correspondiente,observaciones) VALUES (?,?,?,?,?,?)", (cliente_id, monto_f, fecha_str, metodo, mes, obs))
    db.commit(); flash("Pago registrado.", "success"); return redirect(url_for("pagos"))

@app.route("/export/excel")
def export_excel():
    if not logged_in(): return redirect(url_for("login"))
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT p.id, c.nombre as cliente, p.monto, p.fecha_pago, p.metodo_pago, p.mes_correspondiente, p.observaciones, c.estado_servicio FROM pagos p JOIN clientes c ON p.cliente_id = c.id ORDER BY p.id DESC")
    rows = cur.fetchall()
    wb = Workbook(); ws = wb.active; ws.title = "Pagos"; ws.append(["ID","Cliente","Monto","Fecha","Método","Mes","Observaciones","Estado servicio"])
    for r in rows: ws.append([r["id"], r["cliente"], r["monto"], r["fecha_pago"], r["metodo_pago"], r["mes_correspondiente"], r["observaciones"], r["estado_servicio"]])
    bio = io.BytesIO(); wb.save(bio); bio.seek(0)
    return send_file(bio, as_attachment=True, download_name="Reporte_Pagos_TECNOENLACE.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        import sqlite3
        with sqlite3.connect(DB_PATH) as conn:
            pass
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
