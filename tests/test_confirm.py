def test_confirm_reservation(client, hold_reservation):
    # Doğru URL formatı: /reservations/confirm/{id}
    response = client.post(f"/reservations/confirm/{hold_reservation.id}")
    assert response.status_code == 200