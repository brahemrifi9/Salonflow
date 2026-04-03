# 💈 SalonFlow

Production-ready barbershop booking system with WhatsApp integration.

---

## 🚀 Overview

SalonFlow is a real-world booking system designed for barbershops, allowing clients to book appointments directly via WhatsApp while providing businesses with a simple admin interface to manage bookings.

This project is deployed in production and built with a full backend, infrastructure, and messaging integration stack.

---

## 📸 Screenshots

### 📲 WhatsApp Booking Flow
<img src="https://github.com/user-attachments/assets/3469b1e7-6ee7-4e6c-a5a5-73b13fe29049" width="300"/>
<img src="https://github.com/user-attachments/assets/96f9f86c-f877-49f8-877f-f311945f58d5" width="300"/>

### 🖥️ Admin Dashboard
<img src="https://github.com/user-attachments/assets/7c908705-17ab-48e8-84f7-218139faf5f3" width="700"/>

### 📅 Booking Management
<img src="https://github.com/user-attachments/assets/92e61d62-1ca3-4b7e-9cb7-cd67484d599d" width="700"/>

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
