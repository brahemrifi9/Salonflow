Barber Booking System – Requirements Specification
1. Introduction
1.1 Purpose

This document defines the functional and non-functional requirements for the Barber Booking System, a web-based backend application that allows customers to book appointments and administrators to manage them.

This system is designed:

As a production-like backend system for a real barber shop

As an academic software engineering project demonstrating SDLC discipline

As a DevOps portfolio project focusing on containerisation, version control, and deployment

1.2 Scope

The system will provide:

Customer account creation and login

Appointment booking

Appointment cancellation

Double-booking prevention

Administrative appointment overview

Docker-based deployment

The system will initially support a single barber (MVP scope).

2. Stakeholders
Stakeholder	Description
Customers	Users booking appointments
Barber/Admin	Manages appointments
Developer	Maintains and deploys system
3. System Overview

The system is:

A REST API built using FastAPI

Connected to a PostgreSQL database

Containerised using Docker

Managed via GitHub version control

4. Functional Requirements

Each requirement is prioritised using MoSCoW:

M = Must have

S = Should have

C = Could have

W = Won’t have (for MVP)

FR1 – User Registration (M)

The system shall allow users to create an account using:

Email (unique)

Password

Acceptance Criteria:

Duplicate email registration is prevented.

Passwords are securely stored (hashed).

FR2 – User Login (M)

The system shall allow registered users to log in.

Acceptance Criteria:

Authentication returns an access token (JWT).

Invalid credentials return error response.

FR3 – Create Booking (M)

The system shall allow authenticated users to create a booking.

Each booking shall include:

Start date/time

Duration (default 30 minutes)

Acceptance Criteria:

Booking is stored in database.

Booking is linked to user.

Booking cannot be created in the past.

FR4 – Prevent Double Booking (M – Critical)

The system shall prevent overlapping bookings.

Acceptance Criteria:

Two bookings cannot overlap in time.

Conflict results in HTTP 409 response.

Constraint enforced at database level where possible.

FR5 – Cancel Booking (M)

The system shall allow users to cancel their own booking.

Acceptance Criteria:

Booking is marked as cancelled (soft delete).

Cancelled bookings free up the time slot.

FR6 – View User Bookings (S)

Users should be able to view their bookings.

FR7 – Admin View All Bookings (M)

The system shall allow administrators to view all bookings.

Acceptance Criteria:

Only admin users can access.

Returns full appointment list.

FR8 – Health Check Endpoint (M)

The system shall expose a health endpoint for monitoring.

5. Non-Functional Requirements
NFR1 – Security (M)

Passwords must be hashed.

Authentication required for protected routes.

Sensitive configuration stored in environment variables.

NFR2 – Reliability (M)

Database constraints prevent duplicate booking.

Proper error handling implemented.

NFR3 – Scalability (S)

Architecture must allow expansion to multiple barbers in future.

Database design must support indexing on time fields.

NFR4 – Maintainability (M)

Clear project structure.

Separation of routes, models, and services.

Meaningful commit history.

NFR5 – Portability (M)

Application must run via Docker Compose.

No hardcoded credentials.

NFR6 – Observability (S)

Logging configured.

Clear API error responses.

6. Assumptions

Only one barber is supported in MVP.

Appointment duration defaults to 30 minutes.

Opening hours validation may be added later.

7. Constraints

Development time limited to 3 weeks.

System built by single developer.

PostgreSQL selected as database.

FastAPI selected as framework.

8. Traceability Matrix
Requirement	Endpoint	Database Component
FR1	POST /register	users table
FR2	POST /login	users table
FR3	POST /bookings	bookings table
FR4	POST /bookings	unique constraint / overlap logic
FR5	DELETE /bookings/{id}	cancelled_at column
FR7	GET /admin/bookings	bookings table
9. Future Extensions (Out of Scope for MVP)

Multiple barbers

Payment integration

SMS/email notifications

Frontend UI

Availability calendar UI

Rate limiting