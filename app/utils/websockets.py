from app.config import active_connections


async def notify_users(location_id: str, message: dict):
    if active_connections.get(location_id):
        for websocket in active_connections.get(location_id).values():
            try:
                await websocket.send_json(message)
            except:
                pass
