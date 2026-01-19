# Event-Driven CRM System

A multi-tenant CRM (Customer Relationship Management) system built with microservices architecture, GraphQL Federation, and event-driven processing using Kafka.

## Table of Contents

- [Quick Start](#quick-start)
- [Service URLs](#service-urls)
- [Rebuild & Clean Commands](#rebuild--clean-commands)
- [Architecture Overview](#architecture-overview)
- [Company Hierarchy & Access Control](#company-hierarchy--access-control)
- [Test Accounts](#test-accounts)
- [Asynchronous Workflows](#asynchronous-workflows)
- [Testing Strategy](#testing-strategy)
- [Tech Stack](#tech-stack)

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js >= 24.0.0
- Python >= 3.14 (for local development)

### Step-by-Step Setup

```bash
# 1. Install dependencies
npm install

# 2. Start all Docker containers (databases, Kafka, all services)
npm run docker:up

# 3. Initialize databases (run migrations + seed data)
npm run docker:init

# 4. Verify all services are running
npm run docker:ps
```

The system is now running! Open http://localhost:3000 to access the frontend.

### Alternative: Full Setup (Single Command)

```bash
npm run setup:full
```

This runs `npm install`, rebuilds all containers, and initializes databases.

---

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | React CRM Application |
| **GraphQL Gateway** | http://localhost:4000/graphql | Federated GraphQL API |
| **Identity Service** | http://localhost:8001/graphql | Users, Companies, Authentication |
| **CRM Service** | http://localhost:8002/graphql | Customer Management |
| **Audit Service** | http://localhost:8003/graphql | Audit Logs |
| **Notification Service** | http://localhost:8004/graphql | In-App Notifications |
| **Kafka** | localhost:9092 | Message Broker |
| **PostgreSQL (Main)** | localhost:5433 | identity_db, crm_db, audit_db |
| **PostgreSQL (Notifications)** | localhost:5434 | notification_db |

---

## Rebuild & Clean Commands

```bash
# Stop all services
npm run docker:down

# Rebuild and restart all services
npm run docker:rebuild

# Clean rebuild (removes volumes, clears cache, rebuilds from scratch)
npm run docker:clean-rebuild

# View logs
npm run docker:logs

# Check service status
npm run docker:ps
```

### Individual Service Commands

```bash
# Run tests
npm run test              # All services (excluding frontend)
npm run test:crm          # CRM service only
npm run test:identity     # Identity service only
npm run test:shared       # Shared Python library

# Run migrations
npm run migrate           # All services
npm run migrate:identity  # Identity service only
npm run migrate:crm       # CRM service only
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
│                           http://localhost:3000                              │
│                              Apollo Client                                   │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ GraphQL
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GRAPHQL GATEWAY (Apollo)                             │
│                           http://localhost:4000                              │
│                    Federation + JWT Validation                               │
└───────┬─────────────────┬─────────────────┬─────────────────┬───────────────┘
        │                 │                 │                 │
        ▼                 ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   Identity    │ │     CRM       │ │    Audit      │ │ Notification  │
│   Service     │ │   Service     │ │   Service     │ │   Service     │
│  (Django)     │ │  (Django)     │ │  (Django)     │ │  (Django)     │
│  :8001        │ │  :8002        │ │  :8003        │ │  :8004        │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │                 │
        ▼                 │                 │                 │
   PostgreSQL             │                 │                 ▼
   (identity_db)          │                 │            PostgreSQL
                          │                 │         (notification_db)
                          ▼                 ▼
                     PostgreSQL        PostgreSQL
                     (crm_db)          (audit_db)

                          │ Kafka Events
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              KAFKA                                           │
│                          localhost:9092                                      │
│                                                                              │
│  Topics:                                                                     │
│  • crm.customer.created                                                      │
│  • *.dlq.* (Dead Letter Queues)                                             │
└─────────┬─────────────────────┬─────────────────────┬───────────────────────┘
          │                     │                     │
          ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Geocode Worker │   │ Audit Consumer  │   │  Notification   │
│                 │   │                 │   │    Consumer     │
│  Simulates      │   │  Logs all       │   │  Creates in-app │
│  external API   │   │  events         │   │  notifications  │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

### Key Design Decisions

1. **Microservices Architecture**: Each service owns its domain and database, enabling independent scaling and deployment.

2. **GraphQL Federation**: The gateway combines schemas from all services into a unified API, allowing the frontend to query across services seamlessly.

3. **Event-Driven Processing**: User actions publish Kafka events, processed asynchronously by multiple consumers. This decouples services and enables eventual consistency.

4. **JWT Authentication**: Tokens are validated at the gateway and forwarded to services. Each service enforces access control server-side.

5. **Shared Library**: Common utilities (Kafka client, JWT auth) are in `libs/shared-python` to avoid code duplication.

---

## Company Hierarchy & Access Control

The CRM supports a multi-tenant model with parent/child company relationships.

### Company Structure

```
                    ┌─────────────────────┐
                    │   SYSTEM_ADMIN      │
                    │   (No Company)      │
                    │   Sees EVERYTHING   │
                    └─────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
          ▼                                       ▼
┌─────────────────────┐                 ┌─────────────────────┐
│  Acme Corporation   │                 │ GlobalTech Industries│
│  (Parent Company)   │                 │ (Independent Company)│
└─────────┬───────────┘                 └─────────────────────┘
          │                                       │
    ┌─────┴─────┐                          Completely isolated
    │           │                          from Acme hierarchy
    ▼           ▼
┌─────────┐ ┌─────────┐
│  Acme   │ │  Acme   │
│  West   │ │  East   │
│Division │ │Division │
└─────────┘ └─────────┘
```

### Visibility Rules

| User Role | Company | Can See |
|-----------|---------|---------|
| **SYSTEM_ADMIN** | None | ALL data across all companies |
| **COMPANY_ADMIN** (Acme Corp) | Acme Corporation | Acme Corp + West Division + East Division |
| **USER** (West Division) | Acme West Division | West Division + Acme Corporation (parent) |
| **COMPANY_ADMIN** (GlobalTech) | GlobalTech Industries | GlobalTech only (isolated from Acme) |

### What This Means for Data

- **Customers**: Created by a company are visible to that company AND all ancestor companies (parents see children's data)
- **Notifications**: Visible based on the `visible_to_company_ids` field, follows hierarchy rules
- **Audit Logs**: Filtered by company_id, respects hierarchy visibility

### Testing the Hierarchy

1. **Login as Acme Admin** → Create a customer
2. **Login as West Division User** → You can see the customer (parent's data is visible to children)
3. **Login as GlobalTech Admin** → You CANNOT see the customer (different company tree)
4. **Login as System Admin** → You can see ALL customers

---

## Test Accounts

| Role | Email | Password | Company | Access |
|------|-------|----------|---------|--------|
| 🔐 **System Admin** | `admin@crm.com` | `admin123` | All Companies | Full access to everything |
| 🏢 **Acme Admin** | `admin.acme@crm.com` | `acme123` | Acme Corporation | Acme + all child divisions |
| 🏢 **GlobalTech Admin** | `admin.global@crm.com` | `global123` | GlobalTech Industries | GlobalTech only (isolated) |
| 👤 **Regular User** | `user.west@crm.com` | `west123` | Acme West Division | West Division + parent Acme |

---

## Asynchronous Workflows

### Customer Creation Flow

When a customer is created, the following happens asynchronously:

```
User creates customer
        │
        ▼
┌───────────────────┐
│   CRM Service     │
│ 1. Save customer  │
│ 2. Publish event  │
└─────────┬─────────┘
          │ crm.customer.created
          ▼
┌─────────────────────────────────────────────────────────────┐
│                         KAFKA                                │
└─────────┬─────────────────┬─────────────────┬───────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────┐ ┌───────────────┐ ┌───────────────────────┐
│ Geocode Worker  │ │Audit Consumer │ │Notification Consumer  │
│                 │ │               │ │                       │
│ • Geocode addr  │ │ • Log event   │ │ • Create notification │
│ • Update coords │ │               │ │                       │
└─────────────────┘ └───────────────┘ └───────────────────────┘
```

### Notification Service - Kafka for Multi-Channel Notifications

The Notification Service demonstrates how Kafka enables **fan-out messaging** for multi-channel notifications:

```python
# Current implementation: In-app notifications
# The same pattern extends to:
#   - Email notifications (email-consumer)
#   - SMS notifications (sms-consumer)
#   - Mobile push notifications (push-consumer)
```

**Why Kafka for Notifications?**

1. **Decoupling**: The CRM service doesn't need to know about notification channels
2. **Scalability**: Each channel can scale independently
3. **Reliability**: Failed notifications are retried or sent to DLQ
4. **Extensibility**: Add new channels without modifying existing code

**Production Extension Example:**

```
crm.customer.created
        │
        ├──► notification-consumer (in-app) ✓ Implemented
        ├──► email-consumer (SendGrid/SES)  ← Future
        ├──► sms-consumer (Twilio)          ← Future
        └──► push-consumer (FCM/APNS)       ← Future
```

### Geocode Worker - Simulating External API Integration

The Geocode Worker demonstrates handling **external API calls** in an event-driven architecture:

```python
# Simulates calling an external geocoding API (Google Maps, Mapbox, etc.)
# In production, this would make actual API calls:
#
# async with httpx.AsyncClient() as client:
#     response = await client.get(
#         f"https://maps.googleapis.com/maps/api/geocode/json",
#         params={"address": customer_address, "key": API_KEY}
#     )
```

**Key Features Demonstrated:**

1. **Async HTTP Calls**: Uses `httpx.AsyncClient` for non-blocking requests
2. **Retry Logic**: External APIs can fail; the worker retries with exponential backoff
3. **Eventual Consistency**: UI shows "⏳ Pending" until geocoding completes, then "✓ Geocoded"
4. **Service Isolation**: CRM service doesn't wait for geocoding; it happens in the background

### Queue Design Features

The Kafka implementation includes production-ready features:

| Feature | Implementation |
|---------|----------------|
| **Retry with Backoff** | Exponential backoff (2s, 4s, 8s...) up to 60s max |
| **Dead Letter Queue** | Failed messages go to `{topic}.dlq.{consumer_group}` |
| **Error Classification** | `RetryableError` vs `PermanentError` for smart retry decisions |
| **Structured Logging** | JSON logs with topic, partition, offset, event_type |
| **Metrics** | Counters for processed, retried, failed, DLQ messages |
| **Manual Commit** | Offset committed only after successful processing |

---

## Testing Strategy

### Current Test Coverage

Tests are implemented for **important backend logic**:

```bash
# Run all tests
npm run test

# Run specific service tests
npm run test:crm        # 9 tests - mutations, schema, access control
npm run test:identity   # 16 tests - user models, company hierarchy
npm run test:shared     # Kafka client retry logic, DLQ
npm run test:geocode    # Handler error classification
npm run test:gateway    # GraphQL gateway federation
```

### What's Tested

| Service | Tests Cover |
|---------|-------------|
| **CRM Service** | Customer mutations, Kafka event publishing, visibility rules, access control |
| **Identity Service** | User creation, company hierarchy (`get_descendant_ids`, `get_ancestor_ids`), role-based access |
| **Shared Library** | Kafka consumer retry logic, DLQ producer, error handling |
| **Geocode Worker** | Handler logic, error classification (retryable vs permanent) |
| **Gateway** | Federation setup, JWT validation |

### Testing Philosophy

The focus is on testing **critical business logic**:

1. **Access Control**: Users only see data they're authorized to see
2. **Company Hierarchy**: Parent/child relationships work correctly
3. **Event Publishing**: Kafka events are published after mutations
4. **Error Handling**: Retryable vs permanent errors are handled correctly

### Next Steps for Testing

#### 1. Frontend Tests (React Testing Library + Vitest)

```typescript
// Example: Test login flow
describe('LoginPage', () => {
  it('shows error message on invalid credentials', async () => {
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'wrong@email.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('redirects to dashboard on successful login', async () => {
    // Mock Apollo Client
    // Test successful login flow
  });
});
```

#### 2. Integration Tests (End-to-End)

```typescript
// Example: Test full customer creation flow
describe('Customer Creation E2E', () => {
  it('creates customer and triggers async processing', async () => {
    // 1. Login as company admin
    const token = await login('admin.acme@crm.com', 'acme123');
    
    // 2. Create customer via GraphQL
    const customer = await createCustomer(token, { name: 'Test', ... });
    
    // 3. Wait for async processing
    await waitFor(() => {
      const updated = await getCustomer(token, customer.id);
      expect(updated.latitude).toBeDefined();  // Geocoded
    });
    
    // 4. Verify audit log created
    const logs = await getAuditLogs(token);
    expect(logs).toContainEqual(expect.objectContaining({
      eventType: 'crm.customer.created'
    }));
  });
});
```

#### 3. Recommended Testing Tools

| Type | Tool | Purpose |
|------|------|---------|
| **Unit Tests (Python)** | pytest | Backend service logic |
| **Unit Tests (Frontend)** | Vitest + React Testing Library | Component testing |
| **API Tests** | pytest + httpx | GraphQL endpoint testing |
| **E2E Tests** | Playwright or Cypress | Full user flow testing |
| **Load Tests** | k6 or Locust | Performance testing |

---

## Tech Stack

### Backend
- **Python 3.14** - Latest Python with performance improvements
- **Django 5.2** - Web framework
- **Graphene-Django** - GraphQL for Django
- **Graphene-Federation** - Apollo Federation support
- **Confluent-Kafka** - Kafka client
- **PostgreSQL 18** - Primary database
- **Gunicorn** - WSGI server

### Frontend
- **React 18** - UI framework
- **Apollo Client** - GraphQL client
- **React Router** - Navigation
- **Vite** - Build tool

### Infrastructure
- **Apollo Gateway** - GraphQL Federation
- **Kafka** - Message broker
- **Zookeeper** - Kafka coordination
- **Docker & Docker Compose** - Containerization
- **Nx** - Monorepo management

### Testing
- **pytest** - Python testing
- **pytest-django** - Django test utilities
- **Vitest** - JavaScript testing

---

## Project Structure

```
crm-system/
├── apps/
│   ├── crm-frontend/          # React frontend
│   ├── gateway/               # Apollo Federation Gateway
│   ├── identity-service/      # Users, Companies, Auth
│   ├── crm-service/           # Customer management
│   ├── audit-service/         # Audit logging
│   ├── notification-service/  # In-app notifications
│   └── geocode-worker/        # Async geocoding
├── libs/
│   └── shared-python/         # Shared utilities (Kafka, JWT)
├── scripts/                   # Database init scripts
├── docker-compose.yml         # Container orchestration
├── nx.json                    # Nx workspace config
└── package.json               # NPM scripts
```

---

## Troubleshooting

### Services not starting?

```bash
# Check container status
npm run docker:ps

# View logs for specific service
docker-compose logs -f crm-service

# Clean rebuild everything
npm run docker:clean-rebuild
```

### Database connection issues?

```bash
# Reinitialize databases
npm run docker:init
```

### Kafka not processing messages?

```bash
# Check consumer logs
docker-compose logs -f audit-consumer
docker-compose logs -f notification-consumer
docker-compose logs -f geocode-worker
```

---

## License

This project was created as a technical challenge submission.
