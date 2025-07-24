from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import csv
import os

app = Flask(__name__)

# Estado temporal de cada usuario
user_state = {}

# Archivo CSV donde guardamos reservas
RESERVATIONS_FILE = "reservations.csv"

# Crear CSV si no existe
if not os.path.exists(RESERVATIONS_FILE):
    with open(RESERVATIONS_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Phone", "Day", "Time", "Plate"])

def show_menu():
    return ("Bienvenido a *Lavadero Rápido* 🚗\n"
            "¿Qué deseas hacer hoy?\n"
            "1. Reservar un lavado\n"
            "2. Consultar estado de mi carro\n"
            "3. Ver precios y servicios\n"
            "Escribe el número de tu opción.\n"
            "En cualquier momento escribe 'Menú' para volver aquí.")

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get("Body", "").strip().lower()
    from_number = request.values.get("From", "")

    resp = MessagingResponse()
    msg = resp.message()

    # Permitir volver al menú en cualquier momento
    if incoming_msg == "menú" or incoming_msg == "menu":
        user_state[from_number] = {"step": "menu"}
        msg.body(show_menu())
        return str(resp)

    # Si no hay estado previo, iniciar en menú
    if from_number not in user_state:
        user_state[from_number] = {"step": "menu"}
        msg.body(show_menu())
        return str(resp)

    state = user_state[from_number]

    # Flujo principal
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
        # Validación básica: hora debe contener un número
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
                writer.writerow([from_number, state["day"], state["time"], state["plate"]])
            msg.body("¡Tu cita ha sido reservada con éxito! ✅\nTe enviaremos un recordatorio antes de tu turno.\n\n" + show_menu())
            user_state[from_number] = {"step": "menu"}
        elif incoming_msg == "no":
            msg.body("Reserva cancelada. Volviendo al menú principal.\n\n" + show_menu())
            user_state[from_number] = {"step": "menu"}
        else:
            msg.body("Por favor responde 'Sí' para confirmar o 'No' para cancelar.")

    elif state["step"] == "check_status":
        plate = incoming_msg.upper()
        # Aquí podrías integrar una base de datos real para el estado
        msg.body(f"El carro con placa {plate} está: *En proceso de lavado* 🧼\n\n" + show_menu())
        user_state[from_number] = {"step": "menu"}

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
