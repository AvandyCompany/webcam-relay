import asyncio, websockets, os

tela = set()
clientes_cam = set()

async def handler(ws):
    path = ws.path
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
    else:
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
    async with websockets.serve(handler, "0.0.0.0", porta):
        await asyncio.Future()

asyncio.run(main())
