import asyncio, websockets, os

tela = set()
clientes_cam = set()

HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Webcam Remota</title>
<style>body{margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh;overflow:hidden}img{max-width:100%;max-height:100%}#status{position:fixed;top:10px;left:10px;color:#0f0;font-family:monospace;font-size:13px}</style>
</head>
<body>
<img id="v"><div id="status">Conectando...</div>
<script>
const URL = "wss://" + location.host + "/tela";
let ws;
function conectar(){
  ws = new WebSocket(URL);
  ws.onopen = () => document.getElementById("status").textContent = "Conectado";
  ws.onmessage = e => {
    document.getElementById("v").src = "data:image/jpeg;base64," + e.data;
    document.getElementById("status").textContent = "AO VIVO " + new Date().toLocaleTimeString();
  };
  ws.onclose = () => { document.getElementById("status").textContent = "Reconectando..."; setTimeout(conectar, 3000); };
  ws.onerror = () => ws.close();
}
conectar();
</script>
</body></html>"""

async def process_request(connection, request):
    path = request.path
    upgrade = request.headers.get("Upgrade", "").lower()
    # Se NAO for WebSocket -> responde HTML na raiz, 404 no resto
    if upgrade != "websocket":
        if path == "/":
            return (200, [("Content-Type", "text/html; charset=utf-8")], HTML.encode())
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
            # avisa as cameras que tem alguem assistindo
            for c in list(clientes_cam):
                try:
                    await c.send("__RESUME__")
                except:
                    pass
            # fica ouvindo (o cliente nao envia nada, so mantem aberto)
            async for _ in ws:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass  # desconexao normal, nao loga
    except Exception:
        pass  # qualquer outro erro silencioso
    finally:
        clientes_cam.discard(ws)
        if ws in tela:
            tela.discard(ws)
            # se ninguem mais esta vendo, pausa as cameras
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
