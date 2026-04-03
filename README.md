# 💈 SalonFlow

Multi-tenant SaaS platform for barbershops — WhatsApp booking + admin dashboard, built for real business use.

---

## 🚀 Overview

SalonFlow is a production SaaS platform that lets multiple barbershop businesses run independently on shared infrastructure. Each business has its own isolated data, WhatsApp booking flow, and admin panel.

Currently live.

---

## 📸 Screenshots

### 📲 WhatsApp Booking Flow
<img src="https://github.com/user-attachments/assets/3469b1e7-6ee7-4e6c-a5a5-73b13fe29049" width="300"/>
<img src="https://github.com/user-attachments/assets/96f9f86c-f877-49f8-877f-f311945f58d5" width="300"/>

### 🖥️ Admin Dashboard
<img src="https://github.com/user-attachments/assets/7c908705-17ab-48e8-84f7-218139faf5f3" width="700"/>

### 📅 Booking Management
<img src="https://github.com/user-attachments/assets/92e61d62-1ca3-4b7e-9cb7-cd67484d599d" width="700"/>

## 🏢 Multi-Tenant Architecture

Each business is fully isolated at the database level:

- Every tenant table carries a `business_id` foreign key (bookings, barbers, services, clients)
- All API endpoints are scoped to a single business via query param
- Migrations managed with Alembic — schema changes apply across all tenants cleanly
- New businesses can be onboarded without touching existing data

---

## ⚙️ Core Features

### 📅 Booking System
- Business hours: 11:00 – 21:30
- 15-minute time slots
- Lunch break blocking (15:00–16:00)
- Real-time availability calculation
- Booking reference system
- Cancellation system (WhatsApp & admin)
- Automatic client creation
- Overlap protection at database level

**Booking System**
- 15-minute time slots with configurable business hours
- Lunch break blocking
- Real-time availability calculation with overlap protection at DB level
- Booking reference codes
- Cancellation via WhatsApp and admin panel

**WhatsApp Integration**
- Full booking flow via WhatsApp Cloud API (select barber → service → time slot)
- Webhook handling with signature verification
- Multilingual support (ES/EN)
- Permanent access token management

**Admin Panel**
- JWT authentication per business
- Dashboard, booking management, manual booking creation
- Deployed on Vercel

---

### 📲 WhatsApp Integration (Key Feature)
- Integrated with WhatsApp Cloud API
- Fully functional booking flow:
  - Select barber
  - Select service
  - Choose time slot
- Features:
  - Book appointments
  - Cancel bookings
  - View booking details
- Webhook handling with verification
- Permanent access token configured

---

### 🖥️ Admin Panel
- Deployed on Vercel
- Features:
  - Login (JWT authentication)
  - Dashboard
  - Manual booking creation
  - Booking management

---

## 🏗️ Tech Stack

### Backend
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic (database migrations)

### Frontend
- React
- TypeScript
- Vite
- Vercel (deployment)

### Infrastructure
- VPS (Hetzner)
- Docker & Docker Compose
- Nginx (reverse proxy)
- HTTPS (Certbot / Let's Encrypt)
- Cloudflare (proxy + SSL)

---

## 🔐 Security

- UFW firewall enabled
- Fail2Ban protection
- Database not publicly exposed
- HTTPS enforced
- Secure proxy headers configuration

---

## 🌍 Live System

- Admin Panel: https://admin.salonflowapp.com
- API: https://api.salonflowapp.com

---

## 💡 Real-World Usage

This system is designed for real business usage.

A barbershop can currently:
- Accept bookings automatically via WhatsApp
- Manage appointments through the admin panel
- Operate a real booking schedule in production

---

## 🧠 What this project demonstrates

- Full-stack system design
- Real-world backend logic (not CRUD-only)
- Production deployment & infrastructure
- Third-party API integration (WhatsApp)
- Security and system hardening
- Business-oriented software development

---

## 📌 Status

Active MVP — currently being tested with real users and preparing for first client deployments.
