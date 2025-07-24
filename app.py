from flask import Flask, request, render_template_string, redirect, url_for
from twilio.twiml.messaging_response import MessagingResponse
import csv
import os

app = Flask(__name__)

# Estado temporal de conversaciones
user_state = {}

# Archivo de reservas
RESERVATIONS_FILE = "reservations.csv"

# Crear CSV si no existe
if not os.path.exists(RESERVATIONS_FILE):
    with open(RESERVATIONS_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Phone", "Day", "Time", "Plate", "Status"])

def show_menu():
    return ("Bienvenido a *Lavadero Rápido* 🚗\n"
            "¿Qué deseas hacer hoy?\n"
            "1. Reservar un lavado\n"
            "2. Consultar estado de mi carro\n"
            "3. Ver precios y servicios\n"
            "Escribe el número de tu opción.\n"
            "En cualquier momento escribe 'Menú' para volver aquí.")

# ----------- BOT DE WHATSAPP -----------
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get("Body", "").strip().lower()
    from_number = request.values.get("From", "")

    resp = MessagingResponse()
    msg = resp.message()

    # Volver al menú en cualquier momento
    if incoming_msg in ["menú", "menu"]:
        user_state[from_number] = {"step": "menu"}
        msg.body(show_menu())
        return str(resp)

    if from_number not in user_state:
        user_state[from_number] = {"step": "menu"}
        msg.body(show_menu())
        return str(resp)

    state = user_state[from_number]

    if state["step"] == "menu":
        if incoming_msg == "1":
            state["step"] = "day"
            msg.body("¡Perfecto! ¿Qué día deseas agendar tu cita? (Formato DD/MM o escribe 'hoy')")
        elif incoming_msg == "2":
            state["step"] = "check_status"
            msg.body("Por favor, escribe tu placa para verificar el estado de tu carro.")
        elif incoming_msg == "3":
            msg.body("Nuestros servicios disponibles:\n"
                     "- Lavado básico: $25,000\n"
                     "- Lavado completo: $40,000\n"
                     "- Lavado + Polichado: $80,000\n\n"
                     "¿Quieres reservar uno? Escribe '1' para reservar o 'Menú' para volver.")
            state["step"] = "menu"
        else:
            msg.body("Por favor selecciona una opción válida (1, 2 o 3).\n\n" + show_menu())

    elif state["step"] == "day":
        state["day"] = incoming_msg
        state["step"] = "time"
        msg.body("¿A qué hora deseas? Tenemos cupos entre 8:00 am y 5:00 pm (cada hora).")

    elif state["step"] == "time":
        if not any(char.isdigit() for char in incoming_msg):
            msg.body("Por favor ingresa una hora válida (ej: 10:00 am).")
            return str(resp)
        state["time"] = incoming_msg
        state["step"] = "plate"
        msg.body("Por favor escribe la placa de tu carro.")

    elif state["step"] == "plate":
        state["plate"] = incoming_msg.upper()
        state["step"] = "confirm"
        msg.body(f"Por favor confirma tu reserva:\n"
                 f"📅 Día: {state['day']}\n"
                 f"⏰ Hora: {state['time']}\n"
                 f"🚗 Placa: {state['plate']}\n\n"
                 f"Responde 'Sí' para confirmar o 'No' para cancelar.")

    elif state["step"] == "confirm":
        if incoming_msg in ["sí", "si"]:
            with open(RESERVATIONS_FILE, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([from_number, state["day"], state["time"], state["plate"], "En espera"])
            msg.body("¡Tu cita ha sido reservada con éxito! ✅\nTe enviaremos un recordatorio antes de tu turno.\n\n" + show_menu())
            user_state[from_number] = {"step": "menu"}
        elif incoming_msg == "no":
            msg.body("Reserva cancelada. Volviendo al menú principal.\n\n" + show_menu())
            user_state[from_number] = {"step": "menu"}
        else:
            msg.body("Por favor responde 'Sí' para confirmar o 'No' para cancelar.")

    elif state["step"] == "check_status":
        plate = incoming_msg.upper()
        msg.body(f"El carro con placa {plate} está: *En proceso de lavado* 🧼\n\n" + show_menu())
        user_state[from_number] = {"step": "menu"}

    return str(resp)

# ----------- PANEL ADMIN -----------
@app.route("/admin")
def admin_panel():
    key = request.args.get("key")
    if key != "1234":  # Contraseña básica
        return "Acceso no autorizado. Agrega ?key=1234 en la URL."

    reservations = []
    with open(RESERVATIONS_FILE, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            reservations.append(row)

    html = """
    <h1>Panel de Reservas - Lavadero Rápido</h1>
    <table border="1" cellpadding="5">
        <tr>
            <th>Teléfono</th><th>Día</th><th>Hora</th><th>Placa</th><th>Estado</th><th>Acciones</th>
        </tr>
        {% for r in reservations %}
        <tr>
            <td>{{ r['Phone'] }}</td>
            <td>{{ r['Day'] }}</td>
            <td>{{ r['Time'] }}</td>
            <td>{{ r['Plate'] }}</td>
            <td>{{ r['Status'] }}</td>
            <td>
                <a href="{{ url_for('update_status', phone=r['Phone'], status='En espera', key=key) }}">En espera</a> |
                <a href="{{ url_for('update_status', phone=r['Phone'], status='En lavado', key=key) }}">En lavado</a> |
                <a href="{{ url_for('update_status', phone=r['Phone'], status='Listo', key=key) }}">Listo</a>
            </td>
        </tr>
        {% endfor %}
    </table>
    """
    return render_template_string(html, reservations=reservations, key=key)

# ----------- RUTA PARA CAMBIAR ESTADO -----------
@app.route("/update_status")
def update_status():
    key = request.args.get("key")
    if key != "1234":
        return "Acceso no autorizado."

    phone = request.args.get("phone")
    new_status = request.args.get("status")

    # Leer y actualizar el CSV
    rows = []
    with open(RESERVATIONS_FILE, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Phone"] == phone:
                row["Status"] = new_status
            rows.append(row)

    # Escribir de nuevo el CSV actualizado
    with open(RESERVATIONS_FILE, "w", newline="") as file:
        fieldnames = ["Phone", "Day", "Time", "Plate", "Status"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return redirect(url_for("admin_panel", key=key))

if __name__ == "__main__":
    app.run(port=5000, debug=True)
