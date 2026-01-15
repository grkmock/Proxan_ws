def test_create_hold(client):
    # Eğer uygulamanız JWT bekliyorsa geçici bir header ekleyelim
    # Not: conftest'te dependency_override ile auth'u da devre dışı bırakabiliriz 
    # ama şimdilik sembolik bir header deneyelim:
    response = client.post("/reservations/hold", 
        json={"event_id": 1, "user_id": 1},
        headers={"Authorization": "Bearer test-token"} 
    )
    # Eğer hala 401 alırsanız, app/main.py içindeki auth bağımlılığını 
    # conftest.py içinde override etmemiz gerekecek.
    assert response.status_code == 200