import json
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

HOST = "0.0.0.0"
PORT = 6000
MAX_WORKERS = 4

# Simulación de tarea procesada por un hilo del worker
def procesar_tarea(datos_tarea):
    tarea_id = datos_tarea.get("id", "N/A")
    accion = datos_tarea.get("accion", "desconocida")
    parametro = datos_tarea.get("parametro", 0)

    thread_name = threading.current_thread().name
    print(f"[Worker Pool - {thread_name}] Procesando tarea ID {tarea_id}: '{accion}'...")

    # Simulación de tiempo de cómputo/I-O
    time.sleep(1.5)

    if accion == "calcular_factorial":
        import math
        resultado = math.factorial(int(parametro))
    elif accion == "invertir_texto":
        resultado = str(parametro)[::-1]
    else:
        resultado = f"Acción '{accion}' procesada exitosamente."

    print(f"[Worker Pool - {thread_name}] Tarea ID {tarea_id} completada.")
    return {
        "status": "COMPLETED",
        "tarea_id": tarea_id,
        "resultado": resultado,
        "procesado_por": thread_name
    }


def manejar_cliente(conn, addr, pool):
    print(f"[Conexión] Cliente conectado desde {addr}")
    buffer = ""
    try:
        while True:
            data = conn.recv(1024).decode("utf-8")
            if not data:
                break
            
            buffer += data
            # Procesa los mensajes delimitados por \n
            while "\n" in buffer:
                linea, buffer = buffer.split("\n", 1)
                if not linea.strip():
                    continue

                tarea = json.loads(linea)
                print(f"[Dispatcher] Tarea recibida: {tarea}")

                # Enviar tarea al pool de workers concurrentes
                futuro = pool.submit(procesar_tarea, tarea)
                respuesta_datos = futuro.result()

                # Responder al cliente por el socket
                respuesta_json = json.dumps(respuesta_datos) + "\n"
                conn.sendall(respuesta_json.encode("utf-8"))

    except ConnectionResetError:
        print(f"[Aviso] Conexión reseteada por el cliente {addr}")
    except Exception as e:
        print(f"[Error] Fallo en la comunicación con {addr}: {e}")
    finally:
        conn.close()
        print(f"[Desconexión] Socket cerrado para {addr}")


def iniciar_servidor():
    pool = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="WorkerThread")
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(10)
    print(f"[*] Servidor de Tareas iniciado en {HOST}:{PORT}")
    print(f"[*] Pool de Workers listo con {MAX_WORKERS} hilos concurrentes.")

    try:
        while True:
            conn, addr = servidor.accept()
            # Cada cliente se atiende en un hilo dedicado para no bloquear accepts
            hilo_cliente = threading.Thread(target=manejar_cliente, args=(conn, addr, pool))
            hilo_cliente.daemon = True
            hilo_cliente.start()
    except KeyboardInterrupt:
        print("\n[*] Apagando servidor y liberando workers...")
    finally:
        pool.shutdown(wait=True)
        servidor.close()


if __name__ == "__main__":
    iniciar_servidor()