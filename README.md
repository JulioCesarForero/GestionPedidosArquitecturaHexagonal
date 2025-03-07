# Sistema de Gestión de Pedidos - Documentación

## Descripción General

Este proyecto implementa un sistema de gestión de pedidos utilizando una arquitectura moderna de microservicios con las siguientes características:

- **Arquitectura Hexagonal**: Separa el dominio de la aplicación de los detalles técnicos.
- **Microservicios**: Divide la aplicación en servicios independientes y especializados.
- **CQRS (Command Query Responsibility Segregation)**: Separa las operaciones de lectura de las de escritura.
- **Patrón SAGA**: Gestiona transacciones distribuidas entre microservicios.
- **SAGA Log**: Registra eventos de transacciones distribuidas para facilitar la trazabilidad y recuperación.
- **Apache Pulsar**: Broker de mensajes para comunicación asíncrona entre servicios.
- **PostgreSQL**: Base de datos relacional para almacenamiento persistente.
- **Docker**: Contenerización de servicios.
- **Kubernetes**: Orquestación de contenedores para despliegue en GCP.
- **CI/CD**: Integración y despliegue continuo con GitHub Actions.

## Servicios

El sistema está compuesto por los siguientes servicios:

1. **API Gateway**: Punto de entrada único para todas las solicitudes de clientes.
2. **Order Service**: Gestiona los pedidos (creación, consulta, cancelación).
3. **Inventory Service**: Gestiona el inventario de productos.
4. **Payment Service**: Procesa pagos asociados a pedidos.

## Estructura del Proyecto

```
order-management-system/
├── docker-compose.yml
├── infrastructure/
│   ├── pulsar/
│   └── postgres/
├── k8s/
├── services/
│   ├── order-service/
│   ├── inventory-service/
│   └── payment-service/
└── api-gateway/
```

## Requisitos Previos

- Docker y Docker Compose
- Kubernetes CLI (kubectl)
- Google Cloud SDK (para despliegue en GCP)
- Python 3.10
- Git

## Instalación y Ejecución Local

### 1. Clonar el Repositorio

```bash
git clone https://github.com/your-username/order-management-system.git
cd order-management-system
```

### 2. Configurar Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_MULTIPLE_DATABASES=orders,inventory,payments

# Services
ORDER_SERVICE_URL=http://order-service:8000
INVENTORY_SERVICE_URL=http://inventory-service:8000
PAYMENT_SERVICE_URL=http://payment-service:8000
```

### 3. Iniciar con Docker Compose

```bash
docker-compose up -d
```

Este comando iniciará:
- PostgreSQL
- Apache Pulsar
- Servicios de Órdenes, Inventario y Pagos
- API Gateway

### 4. Verificar que todo esté en funcionamiento

```bash
docker-compose ps
```

### 5. Acceder a la API

La API estará disponible en `http://localhost:8080`

## Ejecutar Tests

### Tests Unitarios

```bash
cd services/order-service
python -m pytest tests/unit/ -v
```

### Tests de Integración

```bash
cd services/order-service
python -m pytest tests/integration/ -v
```

### Cobertura de Tests

```bash
cd services/order-service
python -m pytest --cov=src tests/
```

## Despliegue en Kubernetes (GCP)

### 1. Configurar Google Cloud SDK

```bash
gcloud auth login
gcloud config set project [PROJECT_ID]
```

### 2. Crear Cluster GKE

```bash
gcloud container clusters create microservices-cluster \
  --zone us-central1-c \
  --num-nodes 3 \
  --machine-type e2-standard-2
```

### 3. Obtener Credenciales

```bash
gcloud container clusters get-credentials microservices-cluster --zone us-central1-c
```

### 4. Aplicar Configuraciones de Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/pulsar.yaml
kubectl apply -f k8s/order-service.yaml
kubectl apply -f k8s/inventory-service.yaml
kubectl apply -f k8s/payment-service.yaml
kubectl apply -f k8s/api-gateway.yaml
```

### 5. Verificar Despliegue

```bash
kubectl get all -n microservices
```

### 6. Obtener IP del API Gateway

```bash
kubectl get service api-gateway -n microservices
```

## Uso de la API

### Crear un Pedido

```bash
curl -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "customer-123",
    "items": [
      {"product_id": "product-1", "quantity": 2, "unit_price": 10.0},
      {"product_id": "product-2", "quantity": 1, "unit_price": 20.0}
    ]
  }'
```

### Consultar un Pedido

```bash
curl -X GET http://localhost:8080/orders/{order_id}
```

### Cancelar un Pedido

```bash
curl -X POST http://localhost:8080/orders/{order_id}/cancel \
  -H "Content-Type: application/json" \
  -d '{"reason": "Cliente solicitó cancelación"}'
```

## Flujo del Sistema

1. **Creación de Pedido**:
   - Cliente envía solicitud al API Gateway
   - API Gateway reenvía al Order Service
   - Order Service crea pedido con estado CREATED
   - Order Service inicia SAGA y publica evento PaymentRequested
   - Order Service actualiza estado a PENDING_PAYMENT

2. **Procesamiento de Pago**:
   - Payment Service recibe evento PaymentRequested
   - Payment Service procesa el pago
   - Payment Service publica evento PaymentProcessed (éxito/fracaso)
   - Order Service recibe evento PaymentProcessed
   - Si es exitoso, Order Service actualiza estado a PAYMENT_CONFIRMED
   - Order Service publica evento InventoryRequested

3. **Asignación de Inventario**:
   - Inventory Service recibe evento InventoryRequested
   - Inventory Service verifica y asigna inventario
   - Inventory Service publica evento InventoryAllocated (éxito/fracaso)
   - Order Service recibe evento InventoryAllocated
   - Si es exitoso, Order Service actualiza estado a INVENTORY_CONFIRMED

4. **Compensación en caso de Fallo**:
   - Si algún paso falla, se ejecutan acciones compensatorias
   - Ej: Si InventoryAllocated falla, se reembolsa el pago

## Arquitectura Hexagonal

Cada servicio sigue el patrón de Arquitectura Hexagonal (Puertos y Adaptadores):

- **Dominio**: Modelos, lógica de negocio y eventos.
- **Aplicación**: Casos de uso (commands/queries) e interfaces (puertos).
- **Adaptadores**: Implementaciones concretas (API REST, repositorios, mensajería).

## Monitoreo y Logs

Para ver los logs en Docker:

```bash
docker-compose logs -f order-service
```

En Kubernetes:

```bash
kubectl logs -f deployment/order-service -n microservices
```

## Mantenimiento y Escalado

### Escalar un Servicio (Kubernetes)

```bash
kubectl scale deployment order-service --replicas=3 -n microservices
```

### Actualizar un Servicio

```bash
kubectl set image deployment/order-service order-service=new-image:tag -n microservices
```

## Contribuir al Proyecto

1. Haz un fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add some amazing feature'`)
4. Haz push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## Resolución de Problemas

### Problemas Comunes

1. **Los servicios no se comunican entre sí**:
   - Verifica que los nombres de host coincidan con los nombres de servicio
   - Asegúrate de que Pulsar esté funcionando correctamente

2. **Tests de integración fallan**:
   - Verifica que PostgreSQL esté disponible y accesible
   - Confirma que las migraciones de base de datos se hayan ejecutado

3. **Errores de despliegue en Kubernetes**:
   - Revisa los logs con `kubectl logs`
   - Verifica que los secretos y configmaps estén correctamente configurados

## Recursos Adicionales

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de Apache Pulsar](https://pulsar.apache.org/docs/en/standalone/)
- [Arquitectura Hexagonal](https://alistair.cockburn.us/hexagonal-architecture/)
- [Patrón SAGA](https://microservices.io/patterns/data/saga.html)
- [CQRS](https://martinfowler.com/bliki/CQRS.html)