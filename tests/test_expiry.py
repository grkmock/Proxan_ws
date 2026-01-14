def test_expired_hold_cannot_confirm(client, expired_hold):
    response = client.post(
        f"/reservations/{expired_hold['id']}/confirm"
    )

    assert response.status_code == 400
