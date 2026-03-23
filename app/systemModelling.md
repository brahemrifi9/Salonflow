SalonFlow – System Modelling
1. Architectural Overview

SalonFlow follows a layered service-oriented architecture designed to separate concerns and support scalability. The system exposes a REST API and integrates with WhatsApp through the Meta Cloud API.

The architecture consists of the following layers:

Client Layer

API/Webhook Layer

Service (Business Logic) Layer

Persistence Layer

Database Layer

Logical Architecture Diagram
+---------------------------+
|   Customer (WhatsApp)     |
+---------------------------+
             |
             v
+---------------------------+
|   Meta WhatsApp Cloud API |
+---------------------------+
             |
             v
+---------------------------+
| FastAPI Webhook / API     |
| (Routing + Validation)    |
+---------------------------+
             |
             v
+---------------------------+
|  Service Layer            |
|  (Booking Engine, Logic)  |
+---------------------------+
             |
             v
+---------------------------+
|  SQLAlchemy ORM           |
+---------------------------+
             |
             v
+---------------------------+
|  PostgreSQL Database      |
+---------------------------+
Design Rationale

The layered architecture provides several advantages:

Separation of concerns between routing, logic, and persistence.

Improved maintainability, allowing each component to evolve independently.

Testability, as business logic is isolated from the HTTP layer.

Scalability, enabling additional services or frontend applications in the future.

The system supports both API-based interactions and WhatsApp conversational interactions using the same backend services.

2. Deployment Architecture

The system is containerised using Docker Compose, ensuring reproducibility and environment isolation.

Deployment Components

Docker Compose manages the following containers:

API container (FastAPI backend)

Database container (PostgreSQL)

Deployment Diagram
+---------------------------+
|       Docker Compose      |
+---------------------------+
          |        |
          v        v
   +------------+  +------------+
   | FastAPI    |  | PostgreSQL |
   | Container  |  | Container  |
   +------------+  +------------+
          |
          v
+-----------------------------+
| Meta WhatsApp Cloud API     |
+-----------------------------+
Rationale

Containerisation provides:

Environment consistency

Portability across machines

Simple deployment

Isolation of dependencies

Configuration is handled using environment variables, ensuring that sensitive data such as API tokens are not hardcoded.

3. Use Case Diagram

The system has two main actors:

Actors

Customer

interacts through WhatsApp

Admin / Staff

interacts through admin API or future dashboard

Customer Use Cases

View available services

View barbers

Check availability

Create booking

View own bookings

Cancel own booking

Admin / Staff Use Cases

View all bookings

Create booking manually

Cancel booking

Manage barbers

Manage services

4. Data Model (Entity Relationship Overview)

The system uses a relational database to store core entities.

Entities

User

Represents staff or administrators.

Attributes:

id

email

hashed_password

is_admin

Cliente

Represents customers interacting through WhatsApp.

Attributes:

id

telefono

created_at

Barber

Represents barbers working in the shop.

Attributes:

id

name

active

Service

Represents services offered.

Attributes:

id

name

duration_minutes

price

active

Booking

Represents scheduled appointments.

Attributes:

id

cliente_id

barber_id

service_id

start_time

end_time

booking_ref

cancelled_at

WhatsappSession

Stores conversational state for the WhatsApp chatbot.

Attributes:

id

telefono

state

session_data

updated_at

Relationships
Cliente (1) ------ (Many) Booking
Barber  (1) ------ (Many) Booking
Service (1) ------ (Many) Booking

Each booking belongs to:

one client

one barber

one service

5. Sequence Diagram – Booking Creation
Customer → WhatsApp
WhatsApp → Meta Cloud API
Meta → FastAPI Webhook

FastAPI → Booking Service
Booking Service → Database (check availability)
Database → Booking Service

Booking Service → Database (insert booking)
Database → Booking Service

Booking Service → WhatsApp API
WhatsApp API → Customer

If a conflict occurs

Database → Booking Service: conflict detected
Booking Service → API: raise conflict error
API → Customer: booking not available

The system prevents double booking through both:

business logic checks

database constraints

6. Key Design Decisions
Decision 1 – WhatsApp-First Customer Interaction

The system uses WhatsApp as the primary user interface. This allows customers to interact with the system without installing an additional application.

Benefits:

Low barrier to entry

Familiar interface

High adoption rate

Decision 2 – UTC Time Storage

All booking times are stored in UTC.

Local business rules (Madrid time zone) are applied in the application layer.

This avoids:

timezone inconsistencies

daylight saving errors

Decision 3 – Database-Level Booking Protection

Double bookings are prevented through:

overlap validation in the service layer

database constraints

This guarantees data integrity even under concurrent requests.

Decision 4 – Conversation State Machine

The WhatsApp chatbot uses a session-based state machine stored in the database.

This allows the system to track user progress through booking steps such as:

selecting service

selecting barber

selecting date

confirming booking

Decision 5 – Booking Reference System

Each booking receives a unique reference code.

This allows customers to:

identify bookings

cancel bookings

verify bookings

without requiring account registration.


7. Alignment with Requirements

| Requirement           | Model Component      | API Component            |
| --------------------- | -------------------- | ------------------------ |
| User authentication   | User model           | Auth endpoints           |
| Service browsing      | Service model        | Public service endpoints |
| Booking creation      | Booking model        | POST booking endpoint    |
| Availability checking | Booking + Service    | Availability endpoint    |
| Booking cancellation  | Booking.cancelled_at | Cancel endpoint          |
| Admin control         | User.is_admin        | Admin routes             |

