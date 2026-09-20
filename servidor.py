import asyncio, websockets, os

tela = set()
clientes_cam = set()

async def process_request(path, request_headers):
    # Responde à raiz para o health check do Render
    if path == "/":
        return (200, [("Content-Type", "text/plain")], b"Servidor WebSocket Ativo")
    
    # A nova API usa .headers.get() em vez de indexação direta
    upgrade = request_headers.headers.get("Upgrade", "").lower()
    if upgrade != "websocket":
        return (404, [], b"")
    
    return None

async def handler(ws):
    # A CORREÇÃO PRINCIPAL ESTÁ AQUI
    path = ws.request.path
    
    if path == "/cam":
        clientes_cam.add(ws)
        try:
            async for frame in ws:
                for c in list(tela):
                    try:
                        await c.send(frame)
                    except:
                        tela.discard(c)
        finally:
            clientes_cam.discard(ws)
    elif path == "/tela":
        tela.add(ws)
        for c in list(clientes_cam):
            try:
                await c.send("__RESUME__")
            except:
                pass
        try:
            async for _ in ws:
                pass
        finally:
            tela.discard(ws)
            if not tela:
                for c in list(clientes_cam):
                    try:
                        await c.send("__PAUSE__")
                    except:
                        pass

async def main():
    porta = int(os.environ.get("PORT", 8000))
    print(f"--- SERVIDOR NA PORTA {porta} ---")
    async with websockets.serve(
        handler, "0.0.0.0", porta,
        process_request=process_request
    ):
        print("--- PRONTO ---")
        await asyncio.Future()

asyncio.run(main())
