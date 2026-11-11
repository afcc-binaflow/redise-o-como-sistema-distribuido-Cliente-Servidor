# Arquitectura distribuida (PFO3)

```mermaid
flowchart LR
    subgraph Clientes
        WEB[Cliente Web]
        MOV[Cliente Móvil]
        CLI[Cliente de consola]
    end

    LB[Balanceador de carga<br/>Nginx / HAProxy]

    subgraph Servidor
        GW[Servidor de sockets<br/>Gateway TCP]
        Q[Cola de mensajes<br/>RabbitMQ]
        W1[Worker 1<br/>pool de hilos]
        W2[Worker 2<br/>pool de hilos]
        W3[Worker N<br/>pool de hilos]
    end

    subgraph Almacenamiento
        PG[(PostgreSQL)]
        S3[(S3 / almacenamiento de objetos)]
    end

    WEB --> LB
    MOV --> LB
    CLI --> LB
    LB --> GW
    GW --> Q
    Q --> W1
    Q --> W2
    Q --> W3
    W1 --> PG
    W2 --> PG
    W3 --> PG
    W1 --> S3
    W2 --> S3
    W3 --> S3
```

## Flujo de una petición

1. El cliente (web, móvil o consola) abre una conexión TCP al balanceador.
2. El balanceador distribuye la conexión a un servidor gateway.
3. El gateway recibe el mensaje con framing por longitud, lo valida y lo publica en la cola de mensajes (RabbitMQ).
4. Un worker libre consume el mensaje, ejecuta la operación de dominio (registro, login, CRUD de tareas) contra PostgreSQL/S3.
5. El worker publica el resultado en la cola de respuestas (o responde por el canal de la conexión).
6. El gateway devuelve el resultado al cliente y cierra (o mantiene) la conexión.