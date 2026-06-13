
def test_create_alert(client):
    response = client.post("/alerts/", json={
        "patient_id": 1001,
        "alert_type": "sepsis alert",
        "priority": "critical",
        "status": "new",
        "bed": "4",
        "unit": "ICU"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == 1001
    assert data["alert_type"] == "sepsis alert"
    assert data["id"] is not None
    assert data["llm_summary"] is None   # not generated yet

def test_get_alert_not_found(client):
    response = client.get("/alerts/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Alert not found"

def test_acknowledge_alert(client):
    # first create an alert
    create_response = client.post("/alerts/", json={
        "patient_id": 1001,
        "alert_type": "sepsis alert",
        "priority": "critical",
        "status": "new",
        "bed": "4",
        "unit": "ICU"
    })
    alert_id = create_response.json()["id"]

    # then acknowledge it
    patch_response = client.patch(f"/alerts/{alert_id}", json={
        "status": "acknowledged"
    })
    assert patch_response.status_code == 200
    data = patch_response.json()
    assert data["status"] == "acknowledged"
    assert data["acknowledged_at"] is not None