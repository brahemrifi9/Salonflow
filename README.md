# SalonFlow

> Multi-tenant SaaS platform for barbershops — WhatsApp booking + admin dashboard, built for real business use.

![Status](https://img.shields.io/badge/Status-Live%20in%20Production-brightgreen?style=flat-square)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2015-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61DAFB?style=flat-square&logo=react)
![Docker](https://img.shields.io/badge/Infra-Docker%20%2B%20Nginx-2496ED?style=flat-square&logo=docker&logoColor=white)
![WhatsApp](https://img.shields.io/badge/Integration-WhatsApp%20Cloud%20API-25D366?style=flat-square&logo=whatsapp&logoColor=white)

**Admin Panel:** https://admin.salonflowapp.com · **API:** https://api.salonflowapp.com

---

## 🚀 Overview

SalonFlow is a production SaaS platform that lets multiple barbershop businesses run independently on shared infrastructure. Each business has its own isolated data, WhatsApp booking flow, and admin panel.

**Currently live** — first client actively using the system. Second client onboarding in progress.

---

## 📸 Screenshots

### 📲 WhatsApp Booking Flow

<img src="https://github.com/user-attachments/assets/3469b1e7-6ee7-4e6c-a5a5-73b13fe29049" width="300"/> <img src="https://github.com/user-attachments/assets/96f9f86c-f877-49f8-877f-f311945f58d5" width="300"/>

### 🖥️ Admin Dashboard & Booking Management

<img src="https://github.com/user-attachments/assets/7c908705-17ab-48e8-84f7-218139faf5f3" width="700"/>
<img src="https://github.com/user-attachments/assets/92e61d62-1ca3-4b7e-9cb7-cd67484d599d" width="700"/>

---

## ✨ Core Features

| Feature | Description |
|---|---|
| 📲 **WhatsApp Booking** | Full end-to-end booking flow via WhatsApp Cloud API — barber → service → time slot |
| 🏢 **Multi-Tenancy** | Each business runs on shared infrastructure with fully isolated data at the database level |
| 📅 **Smart Scheduling** | 15-minute slots, lunch break blocking, real-time availability, overlap protection at DB level |
| 🔐 **Per-Business Auth** | JWT authentication scoped per business — each tenant has its own admin access |
| 📋 **Booking Management** | Manual booking creation, cancellation via WhatsApp or admin panel, reference code system |
| 🌍 **Multilingual** | WhatsApp flow supports Spanish and English |
| ⚡ **Auto Client Creation** | New clients are created automatically on first booking — zero manual data entry |
| 🔄 **Live Migrations** | Schema changes managed with Alembic — applies across all tenants cleanly |

---

## 🏢 Multi-Tenant Architecture

Each business is fully isolated at the database level:

- Every tenant table carries a `business_id` foreign key (bookings, barbers, services, clients)
- All API endpoints are scoped to a single business via query param
- Migrations managed with Alembic — schema changes apply across all tenants cleanly
- New businesses can be onboarded without touching existing data

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

## 💡 Real-World Usage

A barbershop using SalonFlow can currently:

- Accept bookings automatically via WhatsApp — no staff intervention needed
- Manage all appointments through the admin panel
- Operate a real booking schedule in production with live clients

---

## 🧠 What this project demonstrates

- Multi-tenant SaaS architecture (data isolation, shared infra)
- Real-world backend design — not CRUD-only
- Third-party API integration (WhatsApp Cloud API, webhooks)
- Production deployment & infrastructure management
- Database schema design and migration management (Alembic)
- Security hardening on a live VPS
- Full-stack ownership: backend → infra → frontend → integrations
