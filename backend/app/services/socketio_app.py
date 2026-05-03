import socketio

# Socket.IO server for realtime streaming
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
sio_asgi_app = socketio.ASGIApp(sio, socketio_path="socket.io")


@sio.event
async def connect(sid, environ, auth):
    await sio.emit("server:connected", {"sid": sid}, to=sid)


@sio.event
async def disconnect(sid):
    return


@sio.event
async def analysis_subscribe(sid, data):
    """
    Client subscribes to an analysis room:
      { "analysis_id": 123 }
    """
    analysis_id = (data or {}).get("analysis_id")
    if analysis_id is None:
        return
    await sio.enter_room(sid, f"analysis:{analysis_id}")
    await sio.emit("analysis:subscribed", {"analysis_id": analysis_id}, to=sid)

