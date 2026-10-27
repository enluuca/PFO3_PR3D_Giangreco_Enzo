import json
import socket
import time

SERVER_HOST = "localhost"
SERVER_PORT = 6000

TAREAS_PRUEBA = [
    {"id": 101, "accion": "calcular_factorial", "parametro": 6},
    {"id": 102, "accion": "invertir_texto", "parametro": "SistemasDistribuidos2026"},
    {"id": 103, "accion": "procesar_reporte", "parametro": "datos_paciente_id_44"},
    {"id": 104, "accion": "calcular_factorial", "parametro": 10}
]

def enviar_tareas():
    print(f"[*] Conectando al Servidor Distribuido en {SERVER_HOST}:{SERVER_PORT}...")
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        cliente.connect((SERVER_HOST, SERVER_PORT))
        print("[+] Conexión establecida exitosamente.\n")

        for tarea in TAREAS_PRUEBA:
            print(f"[Cliente] Enviando Tarea ID {tarea['id']}: {tarea['accion']}...")
            mensaje = json.dumps(tarea) + "\n"
            cliente.sendall(mensaje.encode("utf-8"))

            # Recibir la respuesta del servidor
            respuesta_cruda = cliente.recv(1024).decode("utf-8")
            respuesta = json.loads(respuesta_cruda.strip())

            print(f"[Cliente] <-- Respuesta recibida: {respuesta}")
            print(f"          Resultado: {respuesta.get('resultado')}")
            print(f"          Procesador: {respuesta.get('procesado_por')}\n")
            time.sleep(0.5)

    except ConnectionRefusedError:
        print("[Error] No se pudo conectar. Asegúrate de que el servidor esté activo.")
    except Exception as e:
        print(f"[Error inesperado]: {e}")
    finally:
        cliente.close()
        print("[*] Conexión cerrada.")

if __name__ == "__main__":
    enviar_tareas()