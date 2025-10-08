from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Función para conectar a la base de datos
def get_db_connection():
    conn = sqlite3.connect('pagos.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    conn = get_db_connection()
    total_clientes = conn.execute('SELECT COUNT(*) FROM clientes').fetchone()[0]
    activos = conn.execute('SELECT COUNT(*) FROM clientes WHERE estado="Activo"').fetchone()[0]
    cortados = conn.execute('SELECT COUNT(*) FROM clientes WHERE estado="Cortado"').fetchone()[0]
    conn.close()
    return render_template('dashboard.html', total_clientes=total_clientes, activos=activos, cortados=cortados)

@app.route('/clientes')
def clientes():
    conn = get_db_connection()
    lista = conn.execute('SELECT * FROM clientes').fetchall()
    conn.close()
    return render_template('clientes.html', clientes=lista)

@app.route('/pagos')
def pagos():
    conn = get_db_connection()
    lista = conn.execute('SELECT * FROM pagos ORDER BY fecha DESC').fetchall()
    conn.close()
    return render_template('pagos.html', pagos=lista)

# ✅ Nueva ruta: formulario para registrar pago
@app.route('/nuevo_pago')
def nuevo_pago():
    conn = get_db_connection()
    clientes = conn.execute('SELECT id, nombre FROM clientes WHERE estado="Activo"').fetchall()
    conn.close()
    return render_template('nuevo_pago.html', clientes=clientes)

# ✅ Nueva ruta: guardar pago en base de datos
@app.route('/guardar_pago', methods=['POST'])
def guardar_pago():
    cliente_id = request.form['cliente']
    monto = request.form['monto']
    fecha = request.form['fecha']

    conn = get_db_connection()
    conn.execute('INSERT INTO pagos (cliente_id, monto, fecha) VALUES (?, ?, ?)', (cliente_id, monto, fecha))
    conn.commit()
    conn.close()
    return redirect(url_for('pagos'))

@app.route('/salir')
def salir():
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    init_db()   # Crea la tabla si no existe
    fix_db()    # Corrige estructura si falta columna
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


