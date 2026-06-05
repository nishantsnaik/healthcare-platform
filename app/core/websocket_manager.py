from fastapi import WebSocket

class ConnectionManager:

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    def _key(self, caregiver_id: int, device_id: str):
        return f"{caregiver_id}:{device_id}"

    async def connect(self, caregiver_id: int, device_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[self._key(caregiver_id, device_id)] = websocket

    async def disconnect(self, caregiver_id: int, device_id: str):
        self.active_connections.pop(self._key(caregiver_id, device_id))
        pass

    async def send_alert(self, caregiver_id: int, device_id: str, message:str):
        key = self._key(caregiver_id, device_id)
        websocket = self.active_connections.get(key)
        if websocket:
            await websocket.send_text(message)
        else:
            print(f"No connection for {caregiver_id}:{device_id}")


manager = ConnectionManager()