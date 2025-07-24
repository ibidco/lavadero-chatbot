// Configuración de Firebase (reemplaza con tu configuración)
const firebaseConfig = {
    apiKey: "AIzaSyBDJyIFVcyz0jdMqP8jIKkBayQkbapvn48",
    authDomain: "wash-station-e7113.firebaseapp.com",
    databaseURL: "https://wash-station-e7113-default-rtdb.firebaseio.com",
    projectId: "wash-station-e7113",
    storageBucket: "wash-station-e7113.firebasestorage.app",
    messagingSenderId: "703456162474",
    appId: "1:703456162474:web:7c4bd5c101578c61a896d3",
    measurementId: "G-CJPD947Q86"
  };

// Inicializar Firebase
const app = firebase.initializeApp(firebaseConfig);
const database = firebase.database();

// Función para guardar el estado del vehículo
function saveVehicle() {
    const plate = document.getElementById('plate').value;
    const status = document.getElementById('status').value;

    if (plate.trim() === '') {
        alert('Por favor ingrese una placa');
        return;
    }

    const vehicleRef = database.ref('vehicles/' + plate);

    vehicleRef.set({
        plate: plate,
        status: status,
        timestamp: Date.now()  // Timestamp para saber cuándo se actualizó
    }, (error) => {
        const messageDiv = document.getElementById('message');
        if (error) {
            messageDiv.textContent = "Error al guardar los datos: " + error;
            messageDiv.style.color = "red";
        } else {
            messageDiv.textContent = "Estado guardado exitosamente.";
            messageDiv.style.color = "green";
        }
    });
}
