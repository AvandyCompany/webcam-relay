import asyncio, websockets, os

# cameras conectadas: id -> {"ws": ws, "watchers": set(ws_das_telas)}
cameras = {}
# telas conectadas: ws -> id da camera que esta assistindo (ou None)
telas = {}

def lista_cameras():
    return ",".join(sorted(cameras.keys()))

async def enviar_lista_para_todas_telas():
    msg = "LISTA:" + lista_cameras()
    for ws in list(telas.keys()):
        try:
            await ws.send(msg)
        except:
            pass

async def process_request(connection, request):
    path = request.path
    upgrade = request.headers.get("Upgrade", "").lower()
    if upgrade != "websocket":
        if path == "/":
            return (200, [("Content-Type", "text/plain")], b"Servidor WebSocket Ativo")
        return (404, [], b"")
    return None

async def handler(ws):
    path = ws.request.path
    role = None
    cam_id = None
    try:
        if path == "/cam":
            role = "cam"
            primeiro = await ws.recv()
            if not isinstance(primeiro, str) or not primeiro.startswith("ID:"):
                return
            base_id = primeiro[3:].strip() or "sem_nome"
            cam_id = base_id
            n = 1
            while cam_id in cameras:
                n += 1
                cam_id = f"{base_id}_{n}"
            cameras[cam_id] = {"ws": ws, "watchers": set()}
            await enviar_lista_para_todas_telas()

            async for frame in ws:
                watchers = cameras[cam_id]["watchers"]
                for tela_ws in list(watchers):
                    try:
                        await tela_ws.send(frame)
                    except:
                        watchers.discard(tela_ws)

        elif path == "/tela":
            role = "tela"
            telas[ws] = None
            await ws.send("LISTA:" + lista_cameras())
            async for msg in ws:
                if isinstance(msg, str) and msg.startswith("WATCH:"):
                    novo_id = msg[6:].strip()
                    antigo_id = telas.get(ws)

                    if antigo_id and antigo_id in cameras:
                        cameras[antigo_id]["watchers"].discard(ws)
                        if not cameras[antigo_id]["watchers"]:
                            try:
                                await cameras[antigo_id]["ws"].send("__PAUSE__")
                            except:
                                pass

                    telas[ws] = novo_id
                    if novo_id in cameras:
                        primeira_vez = not cameras[novo_id]["watchers"]
                        cameras[novo_id]["watchers"].add(ws)
                        if primeira_vez:
                            try:
                                await cameras[novo_id]["ws"].send("__RESUME__")
                            except:
                                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception:
        pass
    finally:
        if role == "cam" and cam_id:
            info = cameras.pop(cam_id, None)
            if info:
                for tela_ws in list(info["watchers"]):
                    if telas.get(tela_ws) == cam_id:
                        telas[tela_ws] = None
            await enviar_lista_para_todas_telas()
        elif role == "tela":
            antigo_id = telas.pop(ws, None)
            if antigo_id and antigo_id in cameras:
                cameras[antigo_id]["watchers"].discard(ws)
                if not cameras[antigo_id]["watchers"]:
                    try:
                        await cameras[antigo_id]["ws"].send("__PAUSE__")
                    except:
                        pass

async def main():
    porta = int(os.environ.get("PORT", 8000))
    print(f"--- SERVIDOR NA PORTA {porta} ---", flush=True)
    async with websockets.serve(
        handler, "0.0.0.0", porta,
        process_request=process_request
    ):
        print("--- PRONTO ---", flush=True)
        await asyncio.Future()

asyncio.run(main())
