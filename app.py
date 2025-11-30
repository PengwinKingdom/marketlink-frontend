from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from bson import ObjectId
from mongo_conn import usuarios_col
from flask_cors import CORS

load_dotenv()


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.secret_key = os.getenv("FLASK_SECRET", "clave-secreta")

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 1800

DESIGN_MODE = os.getenv("DESIGN_MODE", "0") == "1"

if not DESIGN_MODE:
    from mongo_conn import get_mongo
    



# -------------------- HEALTHCHECK --------------------
@app.route("/health")
def health():
    if DESIGN_MODE:
        return {"db": "MongoDB (simulado)", "mode": "DESIGN_MODE"}
    try:
        client, db = get_mongo()
        client.admin.command("ping")
        return {"db": "ok", "engine": "MongoDB"}
    except Exception as e:
        return {"db": "down", "error": str(e)}, 500


# -------------------- HOME --------------------
@app.route("/")
def home():
    return render_template("home.html")


# -------------------- PLANES PÚBLICO --------------------
@app.route("/planes")
def planes():
    # Esta es la página pública que muestra todos los planes disponibles
    return render_template("planes.html")


# -------------------- REGISTRO --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        company = request.form.get("company", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not company or not email or not password:
            flash("Completa todos los campos.", "error")
            return redirect(url_for("register"))

        if DESIGN_MODE:
            session["user_id"] = "demo_mongo_id"
            session["email"] = email
            session["company"] = company
            flash("✅ (MongoDB simulado) Cuenta creada con éxito.", "success")
            return redirect(url_for("dashboard"))

        # --- Lógica real con MongoDB ---
        try:
            client, db = get_mongo()
            users = db["users"]

            if users.find_one({"email": email}):
                flash("Ese correo ya está registrado.", "error")
                return redirect(url_for("register"))

            users.insert_one({
                "company": company,
                "email": email,
                "password_hash": generate_password_hash(password)
            })

            flash("✅ Cuenta creada con éxito. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for("login"))
            
        except Exception as e:
            flash("Error al crear cuenta. Intenta de nuevo.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


# -------------------- LOGIN --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if DESIGN_MODE:
            if email and password:
                session["user_id"] = "demo_mongo_id"
                session["email"] = email
                session["company"] = (email.split("@")[0] or "MarketLink").title()
                session.permanent = True
                flash("✅ (MongoDB simulado) Inicio de sesión exitoso.", "success")
                return redirect(url_for("dashboard"))
            flash("Completa todos los campos.", "error")
            return redirect(url_for("login"))

        # --- Lógica real con MongoDB ---
        try:
            client, db = get_mongo()
            users = db["users"]

            user = users.find_one({"email": email})
            
            if not user or not check_password_hash(user["password_hash"], password):
                flash("Correo o contraseña incorrectos.", "error")
                return redirect(url_for("login"))

            session["user_id"] = str(user["_id"])
            session["email"] = user["email"]
            session["company"] = user.get("company", "")
            session.permanent = True
            
            flash("✅ Inicio de sesión exitoso.", "success")
            return redirect(url_for("dashboard"))
            
        except Exception as e:
            flash("Error al iniciar sesión. Intenta de nuevo.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


# -------------------- DASHBOARD --------------------
@app.route("/dashboard")
def dashboard():
    # 1) Protege la ruta
    if "user_id" not in session:
        flash("Primero debes iniciar sesión.", "warning")
        return redirect(url_for("login"))

    # 2) Renderiza y envía el flag para ocultar header global
    return render_template(
        "dashboard.html",
        hide_header=True,  # <-- esto oculta el header de base.html
        email=session.get("email", "demo@marketlink.com"),
        company=session.get("company", "MarketLink")
    )


# -------------------- DASHBOARD PLANES (PRIVADO) --------------------
@app.route('/dashboard/planes')
def dashboard_planes():
    # Verificar que el usuario esté autenticado
    if 'user_id' not in session:
        flash("Primero debes iniciar sesión.", "warning")
        return redirect(url_for('login'))
    

    
    # Por ahora todo está hardcodeado en el HTML
    return render_template(
        'dashboard-planes.html', 
        hide_header=True
        )


# -------------------- LOGOUT --------------------
@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("✅ Sesión cerrada.", "info")
    return redirect(url_for("home"))


# -------------------- SOPORTE --------------------
@app.route("/soporte")
def soporte():
    if "user_id" not in session:
        flash("Inicia sesión para ver soporte.", "warning")
        return redirect(url_for("login"))
    return render_template(
        "soporte.html",
        hide_header=True
        )


# -------------------- PERFIL --------------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        flash("Primero debes iniciar sesión.", "warning")
        return redirect(url_for("login"))

    return render_template(
        "profile.html",
        hide_header=True,
        email=session.get("email", "demo@ejemplo.com"),
        company=session.get("company", "Empresa Demo")
    )


def serialize_doc(doc):
    """Convierte ObjectId a str para poder devolver JSON."""
    if not doc:
        return doc
    doc = dict(doc)  # por si es bson.son.SON
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc


@app.route("/usuarios", methods=["POST"])
def crear_usuario_api():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Se requiere un JSON en el cuerpo"}), 400

    usuario = {
        "nombre": data.get("nombre"),
        "email": data.get("email"),
        "password": data.get("password"),
        "rol": data.get("rol", "usuario")
    }

    if not usuario["nombre"] or not usuario["email"] or not usuario["password"]:
        return jsonify({"error": "nombre, email y password son obligatorios"}), 400

    result = usuarios_col.insert_one(usuario)
    usuario["_id"] = result.inserted_id

    return jsonify({
        "message": "Usuario creado",
        "data": serialize_doc(usuario)
    }), 201


@app.route("/usuarios", methods=["GET"])
def listar_usuarios_api():
    usuarios = [serialize_doc(u) for u in usuarios_col.find()]
    return jsonify(usuarios), 200


@app.route("/usuarios/<id_usuario>", methods=["GET"])
def obtener_usuario_api(id_usuario):
    try:
        oid = ObjectId(id_usuario)
    except:
        return jsonify({"error": "ID inválido"}), 400

    usuario = usuarios_col.find_one({"_id": oid})
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    return jsonify(serialize_doc(usuario)), 200


@app.route("/usuarios/<id_usuario>", methods=["PUT"])
def actualizar_usuario_api(id_usuario):
    try:
        oid = ObjectId(id_usuario)
    except:
        return jsonify({"error": "ID inválido"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Se requiere un JSON en el cuerpo"}), 400

    if "_id" in data:
        data.pop("_id")

    result = usuarios_col.update_one({"_id": oid}, {"$set": data})

    if result.matched_count == 0:
        return jsonify({"error": "Usuario no encontrado"}), 404

    usuario_actualizado = usuarios_col.find_one({"_id": oid})
    return jsonify({
        "message": "Usuario actualizado",
        "data": serialize_doc(usuario_actualizado)
    }), 200


@app.route("/usuarios/<id_usuario>", methods=["DELETE"])
def eliminar_usuario_api(id_usuario):
    try:
        oid = ObjectId(id_usuario)
    except:
        return jsonify({"error": "ID inválido"}), 400

    result = usuarios_col.delete_one({"_id": oid})

    if result.deleted_count == 0:
        return jsonify({"error": "Usuario no encontrado"}), 404

    return jsonify({"message": "Usuario eliminado"}), 200


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "API MarketLink OK"}), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    # o:
    # app.run(host="0.0.0.0", port=5000)

