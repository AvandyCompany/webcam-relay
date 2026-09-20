import asyncio, websockets, os

tela = set()
clientes_cam = set()

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
    try:
        if path == "/cam":
            clientes_cam.add(ws)
            async for frame in ws:
                for c in list(tela):
                    try:
                        await c.send(frame)
                    except:
                        tela.discard(c)

        elif path == "/tela":
            tela.add(ws)
            for c in list(clientes_cam):
                try:
                    await c.send("__RESUME__")
                except:
                    pass
            async for _ in ws:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception:
        pass
    finally:
        clientes_cam.discard(ws)
        if ws in tela:
            tela.discard(ws)
            if not tela:
                for c in list(clientes_cam):
                    try:
                        await c.send("__PAUSE__")
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
