def test_create_hold(client):
    response = client.post("/reservations/hold", json={
        "event_id": 1,
        "user_id": 1
    })

    assert response.status_code == 200
    assert response.json()["status"] == "HELD"
