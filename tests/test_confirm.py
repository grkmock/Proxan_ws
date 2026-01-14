def test_confirm_reservation(client, hold_reservation):
    response = client.post(
        f"/reservations/{hold_reservation['id']}/confirm"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"
