def test_expired_hold_cannot_confirm(client, expired_hold):
    # Doğru URL formatı: /reservations/confirm/{id}
    response = client.post(f"/reservations/confirm/{expired_hold.id}")
    assert response.status_code == 400