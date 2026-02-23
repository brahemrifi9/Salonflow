Barber Booking System – System Modelling
1. Architectural Overview

The system follows a layered architecture:

Client → FastAPI (API Layer) → Service Layer → Database (PostgreSQL)

It is containerised using Docker Compose.

Architecture Diagram (Logical View)
+--------------------+
|    Client (HTTP)   |
+--------------------+
           |
           v
+--------------------+
|      FastAPI       |
|  (API Endpoints)   |
+--------------------+
           |
           v
+--------------------+
|   Service Layer    |
| (Business Logic)   |
+--------------------+
           |
           v
+--------------------+
|   SQLAlchemy ORM   |
+--------------------+
           |
           v
+--------------------+
|   PostgreSQL DB    |
+--------------------+

Design Rationale:

Separation of concerns improves maintainability.

Business logic isolated from routing layer.

Database accessed only through ORM.

Allows future scalability (multiple barbers, frontend UI).

2. Deployment Architecture

Docker Compose runs:

api container

postgres container

+-------------------+
|   Docker Compose  |
+-------------------+
      |         |
      v         v
+----------+  +-----------+
| FastAPI  |  | PostgreSQL|
| Container|  | Container |
+----------+  +-----------+

Rationale:

Ensures portability

No hardcoded dependencies

Environment variables used for configuration

3. Use Case Diagram

Primary Actors:

Customer

Admin

Customer Use Cases

Register

Login

Create Booking

Cancel Booking

View Own Bookings

Admin Use Cases

View All Bookings

4. Data Model (ER Overview)

Entities:

User

id

email

hashed_password

is_admin

Booking

id

user_id (FK)

start_time

duration_minutes

cancelled_at

Relationship:

User (1) → (Many) Bookings

5. Sequence Diagram – Booking Creation
User → API: POST /bookings
API → Service: validate request
Service → DB: check for overlapping booking
DB → Service: result
Service → DB: insert booking
DB → Service: success
Service → API: booking created
API → User: 201 Created

If conflict:

DB → Service: constraint violation
Service → API: raise HTTP 409
API → User: 409 Conflict
6. Key Design Decisions
Decision 1 – Single Barber MVP

To reduce complexity and meet time constraints, the system supports one barber in MVP.

Scalability is preserved by designing booking model to allow future barber_id field.

Decision 2 – Database-Level Constraint

Double booking prevention is enforced:

Via uniqueness constraint or overlap check

At database level to ensure reliability

This prevents race conditions.

Decision 3 – Layered Architecture

Separating routes from business logic ensures:

Testability

Maintainability

Clear traceability from requirements to implementation

7. Alignment with Requirements
Requirement	Model Component	API Component
FR1	User model	Auth endpoint
FR3	Booking model	POST /bookings
FR4	DB constraint	Booking service
FR7	User.is_admin	Admin route