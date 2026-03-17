import subprocess, json, time, base64, http.client, os

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
HTML = "file:///D:/IA%20MALELO/orcamentos/2026/SPEEDMAQ/022_SPEEDMAQ_FLANGES_S40/PROPOSTA_COMERCIAL_022_SPEEDMAQ.html"
PDF_OUT = r"D:\IA MALELO\orcamentos\2026\SPEEDMAQ\022_SPEEDMAQ_FLANGES_S40\PROPOSTA_COMERCIAL_022_SPEEDMAQ.pdf"
PORT = 9223

# Launch Edge with remote debugging
proc = subprocess.Popen([
    EDGE, "--headless", "--disable-gpu",
    f"--remote-debugging-port={PORT}",
    "--no-first-run", "--no-default-browser-check",
    "--remote-allow-origins=*",
    HTML
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(3)

# Get websocket target
conn = http.client.HTTPConnection("127.0.0.1", PORT)
conn.request("GET", "/json")
resp = conn.getresponse()
targets = json.loads(resp.read())
conn.close()

ws_url = None
for t in targets:
    if t.get("type") == "page":
        ws_url = t["webSocketDebuggerUrl"]
        break

if not ws_url:
    print("ERROR: no page target found")
    proc.kill()
    exit(1)

# Use websocket to call Page.printToPDF with scale
import websocket
ws = websocket.create_connection(ws_url)

# Wait for page load
ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
ws.recv()
time.sleep(2)

# Print to PDF with scale 0.7 to fit 1 page
ws.send(json.dumps({
    "id": 2,
    "method": "Page.printToPDF",
    "params": {
        "landscape": False,
        "displayHeaderFooter": False,
        "printBackground": True,
        "scale": 0.78,
        "paperWidth": 8.27,
        "paperHeight": 11.69,
        "marginTop": 0.08,
        "marginBottom": 0.08,
        "marginLeft": 0.16,
        "marginRight": 0.16
    }
}))

result = json.loads(ws.recv())
ws.close()
proc.kill()

if "result" in result and "data" in result["result"]:
    pdf_data = base64.b64decode(result["result"]["data"])
    with open(PDF_OUT, "wb") as f:
        f.write(pdf_data)
    print(f"OK: PDF saved ({len(pdf_data)} bytes)")
else:
    print(f"ERROR: {result}")
