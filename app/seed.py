from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app import models
from app.core.security import hash_password


def seed():
    db: Session = SessionLocal()

    try:
        print("🌱 Seeding database...")

        # -----------------------------
        # 1️⃣ Admin user
        # -----------------------------
        admin_email = "admin@salonflow.local"
        admin_password = "Admin123!"

        existing_admin = (
            db.query(models.User)
            .filter(models.User.email == admin_email)
            .first()
        )

        if not existing_admin:
            admin = models.User(
                email=admin_email,
                hashed_password=hash_password(admin_password),
                is_admin=True,
            )
            db.add(admin)
            print("✅ Admin user created")
        else:
            print("⚠️ Admin already exists")

        # -----------------------------
        # 2️⃣ Barbers
        # -----------------------------
        barber_names = ["Carlos", "Miguel", "David"]

        for name in barber_names:
            exists = (
                db.query(models.Barber)
                .filter(models.Barber.name == name)
                .first()
            )

            if not exists:
                db.add(models.Barber(name=name, is_active=True))
                print(f"✅ Barber created: {name}")

        # -----------------------------
        # 3️⃣ Services
        # -----------------------------
        services = [
            {"name": "Corte clásico", "duration": 30, "price": 1500},
            {"name": "Corte + barba", "duration": 45, "price": 2200},
            {"name": "Arreglo de barba", "duration": 20, "price": 1000},
        ]

        for s in services:
            exists = (
                db.query(models.Service)
                .filter(models.Service.name == s["name"])
                .first()
            )

            if not exists:
                db.add(
                    models.Service(
                        name=s["name"],
                        duration_minutes=s["duration"],
                        price_cents=s["price"],
                        is_active=True,
                    )
                )
                print(f"✅ Service created: {s['name']}")

        db.commit()
        print("🌱 Seeding complete.")

    except SQLAlchemyError as e:
        db.rollback()
        print("❌ Database error during seed:")
        print(e)

    finally:
        db.close()


if __name__ == "__main__":
    seed()