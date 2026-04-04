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

---

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

---

### 📲 WhatsApp Integration (Key Feature)

- Full booking flow via WhatsApp Cloud API (select barber → service → time slot)
- Webhook handling with signature verification
- Multilingual support (ES/EN)
- Permanent access token management

---

### 🖥️ Admin Panel

- JWT authentication per business
- Dashboard, booking management, manual booking creation
- Deployed on Vercel

---


## 🛠️ Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, Python, SQLAlchemy ORM |
| Database | PostgreSQL 15, Alembic migrations |
| Frontend | React, TypeScript, Vite |
| Infrastructure | Hetzner VPS, Docker, Nginx |
| DNS / Proxy | Cloudflare |
| Deployment | Backend on VPS (uvicorn), Frontend on Vercel |
| Integration | WhatsApp Cloud API |

---

## 🔐 Security

- UFW firewall + Fail2Ban
- Database not publicly exposed
- HTTPS enforced (Certbot / Let's Encrypt)
- Secure proxy headers via Nginx
- JWT-based admin authentication

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

- Multi-tenant SaaS architecture (data isolation, shared infra)
- Real-world backend design — not CRUD-only
- Third-party API integration (WhatsApp Cloud API, webhooks)
- Production deployment & infrastructure management
- Database schema design and migration management (Alembic)
- Security hardening on a live VPS
- Full-stack ownership: backend → infra → frontend → integrations

---

## 📌 Status

**Live in production** — first client actively using the system. Second client onboarding in progress.
