from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import csv
import os

app = Flask(__name__)

# Estado temporal de usuarios (en memoria)
user_state = {}

# Archivo CSV donde guardamos reservas
RESERVATIONS_FILE = "reservations.csv"

# Inicializar CSV si no existe
if not os.path.exists(RESERVATIONS_FILE):
    with open(RESERVATIONS_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Phone", "Day", "Time", "Plate"])

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "")

    resp = MessagingResponse()
    msg = resp.message()

    # Si el usuario no tiene estado, mostrar menú inicial
    if from_number not in user_state:
        user_state[from_number] = {"step": "menu"}
        msg.body("¡Hola! Bienvenido a *Lavadero Rápido* 🚗\n"
                 "¿Qué te gustaría hacer hoy?\n"
                 "1. Reservar un lavado\n"
                 "2. Consultar el estado de mi carro\n"
                 "3. Ver precios y servicios")
        return str(resp)

    # Recuperar estado actual
    state = user_state[from_number]

    # Flujo principal
    if state["step"] == "menu":
        if incoming_msg == "1":
            state["step"] = "day"
            msg.body("¡Genial! ¿Qué día quieres agendar tu cita? (Formato DD/MM o 'Hoy')")
        elif incoming_msg == "2":
            state["step"] = "check_status"
            msg.body("Por favor, escribe tu placa para verificar el estado del carro.")
        elif incoming_msg == "3":
            msg.body("Nuestros servicios:\n"
                     "- Lavado básico: $25,000\n"
                     "- Lavado completo: $40,000\n"
                     "- Lavado + Polichado: $80,000\n\n"
                     "¿Quieres reservar alguno? (Sí/No)")
            state["step"] = "menu"
        else:
            msg.body("Por favor responde 1, 2 o 3.")
    
    elif state["step"] == "day":
        state["day"] = incoming_msg
        state["step"] = "time"
        msg.body("Perfecto, ¿a qué hora te gustaría? Tenemos cupos entre 8:00 am y 5:00 pm (cada hora).")

    elif state["step"] == "time":
        state["time"] = incoming_msg
        state["step"] = "plate"
        msg.body("Por favor escribe tu placa.")

    elif state["step"] == "plate":
        state["plate"] = incoming_msg

        # Guardar en CSV
        with open(RESERVATIONS_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([from_number, state["day"], state["time"], state["plate"]])

        msg.body(f"¡Listo! Tu cita está agendada para {state['day']} a las {state['time']}.\n"
                 f"Placa: {state['plate']}\n"
                 "Te avisaremos cuando sea tu turno. 🚙")
        
        # Reiniciar estado para que pueda empezar de nuevo
        user_state[from_number] = {"step": "menu"}

    elif state["step"] == "check_status":
        plate = incoming_msg.upper()
        # Aquí podrías conectar con tu sistema real
        msg.body(f"Tu carro con placa {plate} está actualmente: *En proceso de lavado* 🧼")
        user_state[from_number] = {"step": "menu"}

    return str(resp)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
