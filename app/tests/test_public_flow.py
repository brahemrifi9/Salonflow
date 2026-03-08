from datetime import datetime, timezone

def test_public_barbers_services(client):
    r1 = client.get("/api/v1/public/barbers")
    assert r1.status_code == 200
    assert isinstance(r1.json(), list)

    r2 = client.get("/api/v1/public/services")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)


def test_public_booking_creates_client_and_booking(client):
    # You must have at least 1 active barber & service seeded already.
    barbers = client.get("/api/v1/public/barbers").json()
    services = client.get("/api/v1/public/services").json()
    assert len(barbers) > 0
    assert len(services) > 0

    barber_id = barbers[0]["id"]
    service_id = services[0]["id"]

    payload = {
        "telefono": "+34600111222",
        "nombre": "Test Cliente",
        "barber_id": barber_id,
        "service_id": service_id,
        "start_time": "2026-03-10T11:00:00Z",
    }

    r = client.post("/api/v1/public/bookings", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["barber_id"] == barber_id
    assert data["service_id"] == service_id