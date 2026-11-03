#!/usr/bin/env python3
# HassDNS panel — mini-UI tras ingress de HA (la auth ya la hace HA).
# Seguridad: solo escucha el puerto de ingress (supervisor proxyfica y autentica),
# password NUNCA se persiste — solo el api_token resultante (config 600).
import json, os, ssl, urllib.request, http.server, secrets, subprocess

DATA = "/data/panel_config.json"
API  = "https://hassdns.com"

def load_cfg():
    try: return json.load(open(DATA))
    except Exception: return {}

def save_cfg(c):
    tmp = DATA + ".tmp"
    with open(tmp, "w") as f: json.dump(c, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, DATA)

def api_register(email, pw):
    req = urllib.request.Request(API + "/api_register.php",
        data=json.dumps({"email": email, "password": pw}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def api_login(user, pw):
    req = urllib.request.Request(API + "/api_login.php",
        data=json.dumps({"user": user, "pass": pw}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

PAGE = """<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>HassDNS</title><style>
body{background:#0d1117;color:#dce3ea;font-family:system-ui;margin:0;padding:24px;max-width:560px}
h1{color:#2dd4bf;font-size:1.3rem} .card{background:#151b24;border:1px solid #212b38;border-radius:12px;padding:18px;margin:12px 0}
label{display:block;font-size:.75rem;color:#8b98a8;margin:10px 0 4px;text-transform:uppercase}
input,select{width:100%;box-sizing:border-box;background:#0d1117;border:1px solid #2b3644;border-radius:8px;color:#dce3ea;padding:10px}
button{background:#0d9488;border:0;border-radius:8px;color:#fff;padding:11px 18px;font-weight:700;cursor:pointer;margin-top:14px}
.err{color:#f87171;font-size:.85rem}.ok{color:#34d399;font-size:.85rem}.dom{display:flex;gap:8px;align-items:center;padding:6px 0}
.dom input{width:auto}a{color:#38bdf8}</style></head><body>
<h1>HassDNS DNS</h1>__BODY__
<p style="font-size:.75rem;color:#57606c;margin-top:24px">Sin cuenta: <a href="https://hassdns.com" target=_blank>regístrate en hassdns.com</a></p></body></html>"""

def page_logged(cfg):
    doms = cfg.get("domains", [])
    rows = "".join(f'<div class=dom><input type=checkbox checked disabled><span>{d["name"]} <small style="color:#57606c">({d.get("type","A")})</small></span></div>' for d in doms)
    return ("<div class=card><div class=ok>&#10003; Sesión activa — " + str(len(doms)) + " dominio(s) en uso</div>"
        + rows + '<form method=POST action=/logout><button>Cerrar sesión</button></form></div>'
        + '<div class=card style="font-size:.8rem;color:#8b98a8">El add-on actualiza estos dominios y renueva el cert LE automáticamente.</div>')

def page_login(err=""):
    return (("<div class=err>"+err+"</div>" if err else "") +
        '<div class=card><form method=POST action=/login><label>Usuario / email</label><input name=u required autocomplete=username>'
        '<label>Contraseña</label><input name=p type=password required autocomplete=current-password>'
        '<button>Iniciar sesión</button></form>'
        '<details style="margin-top:16px"><summary style="cursor:pointer;color:#38bdf8;font-size:.85rem">¿Sin cuenta? Regístrate</summary>'
        '<form method=POST action=/register style="margin-top:12px"><label>Email</label><input name=e type=email required autocomplete=email>'
        '<label>Contraseña (mín. 8)</label><input name=p2 type=password required minlength=8 autocomplete=new-password>'
        '<button>Crear cuenta</button></form></details></div>')

class H(http.server.BaseHTTPRequestHandler):
    def _send(self, body, code=200, ctype="text/html"):
        if isinstance(body, str): body = body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
    def _form(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 8192: return {}
        from urllib.parse import parse_qs
        return {k: v[0] for k, v in parse_qs(self.rfile.read(n).decode()).items()}
    def do_GET(self):
        if self.path != "/": return self._send(b"404", 404)
        cfg = load_cfg()
        self._send(PAGE.replace("__BODY__", page_logged(cfg) if cfg.get("api_token") else page_login()))
    def do_POST(self):
        if self.path == "/logout": save_cfg({}); return self._send('<meta http-equiv=refresh content="0;url=/">')
        if self.path == "/register":
            f = self._form()
            e, p2 = (f.get("e", "").strip().lower(), f.get("p2", ""))
            if not e or len(p2) < 8:
                return self._send(PAGE.replace("__BODY__", page_login("Email o contraseña corta (mín. 8)")))
            r = api_register(e, p2)
            if not r.get("ok"):
                return self._send(PAGE.replace("__BODY__", page_login(r.get("error") or "No se pudo registrar")))
            r2 = api_login(e, p2)
            if r2.get("ok"):
                save_cfg({"api_token": r2["api_token"], "domains": r2.get("domains", [])})
                return self._send('<meta http-equiv=refresh content="0;url=/">')
            return self._send(PAGE.replace("__BODY__", page_login("Cuenta creada — inicia sesión")))
        if self.path != "/login": return self._send(b"404", 404)
        f = self._form()
        u, p = (f.get("u", "").strip(), f.get("p", ""))
        if not u or not p:
            return self._send(PAGE.replace("__BODY__", page_login("Faltan credenciales")))
        r = api_login(u, p)
        if not r.get("ok"):
            return self._send(PAGE.replace("__BODY__", page_login(r.get("error") or "Credenciales incorrectas")))
        save_cfg({"api_token": r["api_token"], "domains": r.get("domains", [])})
        self._send('<meta http-equiv=refresh content="0;url=/">')

http.server.HTTPServer(("0.0.0.0", 8099), H).serve_forever()
