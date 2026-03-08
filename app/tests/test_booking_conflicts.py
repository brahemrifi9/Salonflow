def test_booking_lunch_blocked(client):
    barbers = client.get("/api/v1/public/barbers").json()
    services = client.get("/api/v1/public/services").json()
    assert len(barbers) > 0
    assert len(services) > 0

    payload = {
        "telefono": "+34600999999",
        "nombre": "Lunch Tester",
        "barber_id": barbers[0]["id"],
        "service_id": services[0]["id"],
        # 15:00Z might not be lunch in Spain depending on timezone/DST,
        # so pick a time you KNOW your validator blocks. If your validator expects UTC
        # but checks Madrid hours, keep using your known failing sample.
        "start_time": "2026-03-10T14:30:00Z",
    }

    r = client.post("/api/v1/public/bookings", json=payload)
    assert r.status_code in (400, 422)


def test_booking_overlap_returns_409(client):
    barbers = client.get("/api/v1/public/barbers").json()
    services = client.get("/api/v1/public/services").json()
    assert len(barbers) > 0
    assert len(services) > 0

    barber_id = barbers[0]["id"]
    service_id = services[0]["id"]

    # First booking
    p1 = {
        "telefono": "+34600123000",
        "nombre": "Overlap Tester",
        "barber_id": barber_id,
        "service_id": service_id,
        "start_time": "2026-03-10T12:00:00Z",
    }
    r1 = client.post("/api/v1/public/bookings", json=p1)
    assert r1.status_code == 201

    # Overlapping booking (same barber)
    p2 = {
        "telefono": "+34600123001",
        "nombre": "Overlap Tester 2",
        "barber_id": barber_id,
        "service_id": service_id,
        "start_time": "2026-03-10T12:15:00Z",
    }
    r2 = client.post("/api/v1/public/bookings", json=p2)
    assert r2.status_code == 409