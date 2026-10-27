# PFO 3: Rediseño como Sistema Distribuido (Cliente-Servidor con Sockets)

> [!NOTE]
> **Materia:** Programación sobre Redes  
> **Tecnologías:** Python 3, Sockets TCP, ThreadPoolExecutor, JSON, Multithreading  
> **Patrón Arquitectónico:** Dispatcher-Worker / Distributed Task Queue  

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Sockets](https://img.shields.io/badge/Network-TCP%20Sockets-0ea5e9)
![Architecture](https://img.shields.io/badge/Pattern-Dispatcher--Worker-0284c7)
![Status](https://img.shields.io/badge/Estado-Completado-2563eb)

---

## 1. Descripción del Proyecto
Este proyecto implementa el rediseño del sistema transformándolo en una **arquitectura distribuida** basada en sockets TCP y procesamiento concurrente.

El sistema resuelve el desacople entre la recepción de eventos en red y el procesamiento computacional intensivo:
- **Servidor (Dispatcher + Worker Pool):** Escucha conexiones entrantes sobre sockets stream TCP, parsea flujos de mensajes JSON delimitados por salto de línea (`\n`) y delega el cómputo a un conjunto administrado de hilos de trabajo (`ThreadPoolExecutor`) sin bloquear el socket principal.
- **Cliente (Task Producer):** Genera y despacha paquetes de trabajo estructurados, recibiendo las respuestas procesadas de forma síncrona/asíncrona.
- **Diseño de Escala:** Propone la integración con componentes de producción: Balanceador de carga (**Nginx/HAProxy**), Message Broker (**RabbitMQ**) y capas de persistencia distribuida (**PostgreSQL** para metadatos transaccionales y **AWS S3 / MinIO** para objetos pesados).

---

## 2. Diagrama de la Arquitectura Distribuida

```text
[ Clientes Móviles / Web ]
             │
             │ (HTTP/S o TCP)
             ▼
┌────────────────────────────────────────┐
│   Load Balancer (Nginx / HAProxy)      │
└────────────────────────────────────────┘
             │ (Round Robin / Least Connections)
             ▼
┌────────────────────────────────────────┐
│     Servidores API / Gateways          │
└────────────────────────────────────────┘
             │
             │ (Publicación de tareas pendientes)
             ▼
┌────────────────────────────────────────┐
│   Message Broker (RabbitMQ)            │
│   - Queue: 'task_queue'                │
└────────────────────────────────────────┘
             │
             │ (AMQP / Consumo concurrente)
             ▼
┌────────────────────────────────────────────────────────┐
│   Servidores Workers (Clúster de Procesamiento)        │
│                                                        │
│  ┌─────────────────────────┐ ┌───────────────────────┐ │
│  │ Worker Node 1           │ │ Worker Node 2         │ │
│  │ [Thread Pool: T1,T2..Tn]│ │ [Thread Pool: T1..Tn] │ │
│  └────────────┬────────────┘ └───────────┬───────────┘ │
└───────────────┼──────────────────────────┼─────────────┘
                │                          │
        ┌───────┴──────────┐       ┌───────┴──────────┐
        ▼                  ▼       ▼                  ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│ Base de Datos Relacional    │ │ Almacenamiento de Objetos   │
│ (PostgreSQL Distribuido)    │ │ (AWS S3 / MinIO)            │
│ - Metadatos, estados, logs  │ │ - Archivos, imágenes, blobs │
└─────────────────────────────┘ └─────────────────────────────┘
```

### Componentes de la Arquitectura
1. **Clientes (Móviles / Web):** Dispositivos y aplicaciones que envían peticiones de ejecución de tareas o procesamiento de datos.
2. **Balanceador de Carga (HAProxy / Nginx):** Distribuye las conexiones de red entrantes entre múltiples instancias de la capa de entrada para evitar cuellos de botella y garantizar alta disponibilidad.
3. **Cola de Mensajes (RabbitMQ):** Actúa como buffer asíncrono y desacoplador. Permite la persistencia de mensajes (ACKs), el reintento automático y la distribución equitativa de carga (*fair dispatch*) hacia los nodos workers.
4. **Servidores Workers (Pool de Hilos):** Procesos encargados de consumir tareas desde la cola y ejecutarlas concurrentemente utilizando `ThreadPoolExecutor`.
5. **Almacenamiento Distribuido:**
   - **PostgreSQL:** Persistencia relacional ACID para estados de tareas, trazabilidad, logs y credenciales.
   - **AWS S3 / MinIO:** Almacén de objetos distribuido de alta durabilidad para insumos y resultados binarios o de gran volumen (archivos, reportes, imágenes).

---

## 3. Estructura del Repositorio

```text
├── capturas/
│   ├── servidor_consola.png      # Ejecución del servidor y asignación a WorkerThreads
│   ├── cliente_consola.png       # Envío y recepción de tareas desde el cliente
│   └── arquitectura.png          # Exportación gráfica del diagrama distribuido
├── servidor_distribuido.py       # Servidor TCP socket con ThreadPoolExecutor
├── cliente_distribuido.py        # Cliente emisor de tareas vía sockets
└── README.md                     # Documentación técnica de la entrega
```

---

## 4. Requisitos y Dependencias

* **Python 3.8 o superior**.
* La implementación utiliza exclusivamente módulos de la **biblioteca estándar de Python**:
  - `socket`: Manejo de comunicaciones de red TCP/IP en capa de transporte.
  - `threading`: Gestión de hilos de atención a clientes.
  - `concurrent.futures.ThreadPoolExecutor`: Pool de hilos de trabajo gestionado para tareas concurrentes.
  - `json`: Serialización y deserialización de datos estructurados.
  - `time` / `math`: Simulación de carga computacional y operaciones matemáticas.

No se requiere la instalación de librerías de terceros vía `pip`.

---

## 5. Instrucciones de Ejecución

### 1. Iniciar el Servidor de Tareas
En una primera terminal, situarse en el directorio del proyecto y ejecutar:

```bash
python servidor_distribuido.py
```

* El servidor abrirá un socket en `0.0.0.0:6000`.
* Se inicializará un pool con 4 workers concurrentes (`WorkerThread_0` a `WorkerThread_3`).

### 2. Ejecutar el Cliente Emisor
En una segunda terminal, ejecutar:

```bash
python cliente_distribuido.py
```

El cliente conectará al socket TCP local, enviará una batería de tareas en formato JSON delimitadas por `\n` y aguardará la recepción de los resultados calculados.

---

## 6. Formato del Protocolo de Comunicación (JSON sobre TCP)

### Tarea Enviada (Cliente -> Servidor)
```json
{
  "id": 101,
  "accion": "calcular_factorial",
  "parametro": 6
}
```

### Resultado Retornado (Servidor -> Cliente)
```json
{
  "status": "COMPLETED",
  "tarea_id": 101,
  "resultado": 720,
  "procesado_por": "WorkerThread_0"
}
```

---

## 7. Justificación Técnica

> [!NOTE]
> ### Manejo de Concurrencia y Bloqueos
> El uso de un hilo dedicado por conexión de cliente (`threading.Thread`) combinado con un `ThreadPoolExecutor` evita que tareas con alta carga de CPU o I/O bloqueen la recepción de nuevas conexiones en `socket.accept()`. Si una tarea toma tiempo en procesar, las demás continúan despachándose en los hilos restantes del pool.