from app.models.alert import Alert

alerts_db: dict[int, Alert] = {}
alert_counter: int = 0

def fetch_alert(alert_id: int) -> Alert|None:
    return alerts_db.get(alert_id)

def save_alert(alert: Alert) -> Alert:
    alerts_db[alert.id] = alert
    return alert

def get_next_int() -> int:
    global alert_counter
    alert_counter += 1
    return alert_counter
