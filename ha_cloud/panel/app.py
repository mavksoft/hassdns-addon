#!/usr/bin/env python3
# HassDNS panel — mini-UI tras ingress de HA (la auth ya la hace HA).
# Seguridad: solo escucha el puerto de ingress (supervisor proxyfica y autentica),
# password NUNCA se persiste — solo el api_token resultante (config 600).
import json, os, ssl, urllib.request, urllib.error, http.server, secrets, subprocess, threading

DATA = "/data/panel_config.json" if os.path.exists("/data") else "/tmp/panel_config.json"
API  = "https://hassdns.com"
SUP       = "http://supervisor"
SUP_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")

def load_cfg():
    try: return json.load(open(DATA))
    except Exception: return {}

def save_cfg(c):
    tmp = DATA + ".tmp"
    with open(tmp, "w") as f: json.dump(c, f)
    try: os.chmod(tmp, 0o600)
    except Exception: pass
    os.replace(tmp, DATA)

def _log(*a):
    print("[panel]", *a, flush=True)

def _sup(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(SUP + path, data=data, method=method,
        headers={"Authorization": "Bearer " + SUP_TOKEN, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        # El cuerpo del Supervisor dice POR QUÉ (validación, permisos…).
        raise RuntimeError("HTTP %s: %s" % (e.code, e.read().decode(errors="replace")[:300]))

def _restart():
    try:
        _sup("POST", "/addons/self/restart"); _log("reinicio del add-on solicitado")
    except Exception as e:
        _log("reinicio FALLO:", e)

def ha_apply(domains, token):
    # Escribe domains/token en las OPCIONES del add-on (lo que ve la pestaña
    # Configuración) y reinicia para aplicarlas: fuente única = opciones del add-on.
    if not SUP_TOKEN:
        _log("ha_apply: NO hay SUPERVISOR_TOKEN (¿falta hassio_api en config.yaml, o add-on sin actualizar?)")
        return False
    try:
        info = _sup("GET", "/addons/self/info")
        opts = (info.get("data") or {}).get("options") or {}
    except Exception as e:
        _log("ha_apply: GET self/info falló:", e); opts = {}
    opts["domains"] = domains
    opts["token"]   = token
    try:
        _sup("POST", "/addons/self/options", {"options": opts})
        _log("ha_apply: opciones escritas OK →", domains)
    except Exception as e:
        _log("ha_apply: POST options FALLÓ →", e)
        return False
    # El reinicio mata este proceso: con retardo para que la respuesta HTTP
    # (POST→Redirect→GET) termine antes en el navegador.
    threading.Timer(3.0, _restart).start()
    return True

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

PAGE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HassDNS · Home Assistant</title>
<link rel="icon" type="image/png" href="https://hassdns.com/android-chrome-192x192.png">
<link rel="preconnect" href="https://api.fontshare.com">
<link rel="preconnect" href="https://cdn.fontshare.com" crossorigin>
<link href="https://api.fontshare.com/v2/css?f[]=general-sans@400,500,600,700&display=swap" rel="stylesheet">
<style>
:root{
  color-scheme:dark;
  --bg:#07090e;--surface:#131a1f;--surface-2:#182128;--ink:#f4f7f8;--muted:#a9bcc4;
  --accent:#22d3ee;--accent-ink:#04141a;--line:#22303a;--ok:#2dd4bf;--bad:#f87171;--radius:10px;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{min-height:100vh}
body{
  background:linear-gradient(rgba(10,14,17,.72), rgba(10,14,17,.86)), url('https://hassdns.com/login-bg.jpg') center / cover no-repeat fixed var(--bg);
  color:var(--ink);
  font:400 15px/1.45 'General Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  -webkit-font-smoothing:antialiased;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  align-items:center;
  padding:16px 20px;
}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.top-nav{
  width:100%;
  max-width:960px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:8px 0 16px;
  gap:12px;
}
.wordmark{
  display:flex;
  align-items:center;
  gap:10px;
  font-weight:700;
  font-size:1.15rem;
  letter-spacing:-.01em;
  color:var(--ink);
  text-decoration:none;
}
.wordmark img{width:32px;height:32px;border-radius:7px;display:block}
.wordmark span b{color:var(--accent);font-weight:700}
.btn-back{
  display:inline-flex;
  align-items:center;
  gap:8px;
  background:rgba(24,33,40,0.85);
  color:var(--muted);
  border:1px solid rgba(255,255,255,0.08);
  border-radius:999px;
  padding:8px 16px;
  font:600 .88rem 'General Sans',sans-serif;
  cursor:pointer;
  transition:all .18s ease;
  backdrop-filter:blur(8px);
  -webkit-backdrop-filter:blur(8px);
  text-decoration:none;
}
.btn-back:hover{
  background:rgba(34,211,238,0.15);
  color:var(--accent);
  border-color:rgba(34,211,238,0.35);
  transform:translateX(-2px);
  text-decoration:none;
}
main{
  flex:1;
  display:flex;
  flex-direction:column;
  justify-content:center;
  align-items:center;
  width:100%;
  padding:16px 0;
}
.card{
  width:100%;
  max-width:440px;
  background:rgba(19,26,31,0.92);
  backdrop-filter:blur(14px);
  -webkit-backdrop-filter:blur(14px);
  border:1px solid rgba(255,255,255,0.08);
  box-shadow:0 16px 48px rgba(0,0,0,0.55);
  border-radius:14px;
  padding:28px 24px;
  box-sizing:border-box;
}
.card-nav{
  display:flex;
  justify-content:flex-start;
  margin-bottom:14px;
}
.card-nav .back-link{
  display:inline-flex;
  align-items:center;
  gap:6px;
  background:transparent;
  border:0;
  color:var(--muted);
  font:500 .85rem 'General Sans',sans-serif;
  cursor:pointer;
  padding:0;
}
.card-nav .back-link:hover{color:var(--accent);text-decoration:none}
h1{font-size:1.6rem;font-weight:700;letter-spacing:-.02em;margin:0 0 6px}
p.mut{color:var(--muted);font-size:.92rem;line-height:1.4;margin:0 0 18px}
.flash{padding:12px 14px;border-radius:8px;font-size:.88rem;margin-bottom:16px;line-height:1.35}
.flash.bad{background:rgba(248,113,113,0.12);color:#ffd9d9;border:1px solid rgba(248,113,113,0.3)}
.flash.ok{background:rgba(45,212,191,0.12);color:#eafcff;border:1px solid rgba(45,212,191,0.3)}
form.stack{display:flex;flex-direction:column;gap:14px}
label{display:flex;flex-direction:column;gap:6px;font-size:.85rem;color:var(--muted);font-weight:500}
input:not([type=checkbox]):not([type=radio]):not([type=submit]):not([type=button]),
select, textarea {
  width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--line);
  color:var(--ink);border-radius:8px;padding:11px 13px;font:inherit;font-size:.95rem;
  line-height:1.4;height:44px;transition:border-color .15s,box-shadow .15s;
}
input:focus,select:focus,textarea:focus{border-color:var(--accent);outline:none;box-shadow:0 0 0 3px rgba(34,211,238,.18)}
input:-webkit-autofill,
input:-webkit-autofill:hover, 
input:-webkit-autofill:focus, 
input:-webkit-autofill:active {
  -webkit-box-shadow: 0 0 0 1000px #07090e inset !important;
  -webkit-text-fill-color: #f4f7f8 !important;
  caret-color: #f4f7f8 !important;
  transition: background-color 5000s ease-in-out 0s;
}
button.btn-primary{
  display:inline-flex;align-items:center;justify-content:center;gap:8px;
  background:var(--accent);color:var(--accent-ink);border:0;border-radius:var(--radius);
  padding:12px 20px;font:700 .95rem 'General Sans',sans-serif;cursor:pointer;
  transition:transform .18s,background .18s;width:100%;margin-top:6px;
}
button.btn-primary:hover{background:#38e1fc;transform:translateY(-1px)}
button.btn-secondary{
  display:inline-flex;align-items:center;justify-content:center;gap:8px;
  background:var(--surface-2);color:var(--ink);border:1px solid var(--line);border-radius:var(--radius);
  padding:10px 18px;font:600 .9rem 'General Sans',sans-serif;cursor:pointer;
  transition:background .18s;width:100%;
}
button.btn-secondary:hover{background:#223039}
button.btn-bad{
  display:inline-flex;align-items:center;justify-content:center;
  background:transparent;color:var(--bad);border:1px solid rgba(248,113,113,0.3);
  border-radius:8px;padding:9px 16px;font:600 .85rem 'General Sans',sans-serif;cursor:pointer;
  transition:all .18s;
}
button.btn-bad:hover{background:rgba(248,113,113,0.12)}
.dom-row{
  display:flex;flex-direction:row;align-items:center;gap:10px;padding:10px 12px;background:var(--bg);
  border:1px solid var(--line);border-radius:8px;margin-bottom:8px;
}
.dom-tag{
  background:var(--surface-2);color:var(--accent);border:1px solid rgba(34,211,238,0.25);
  padding:2px 8px;border-radius:6px;font-size:.75rem;font-weight:700;
}
.dom-name{flex:1;font-size:.95rem;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dom-badge{color:var(--ok);font-size:.8rem;font-weight:600}
.foot{color:#57606c;font-size:.78rem;text-align:center;padding:12px 0;width:100%}
.foot a{color:#8b98a8;text-decoration:none}
.foot a:hover{color:var(--accent);text-decoration:underline}
details{margin-top:16px;border-top:1px solid var(--line);padding-top:14px}
details summary{cursor:pointer;color:var(--muted);font-size:.85rem;text-align:center}
details summary:hover{color:var(--accent)}
</style>
<script>
function goBackHA() {
  try {
    if (window.parent && window.parent !== window) {
      window.parent.history.back();
      return;
    }
  } catch (e) {}
  try {
    if (window.top && window.top !== window) {
      window.top.history.back();
      return;
    }
  } catch (e) {}
  window.history.back();
}
</script>
</head>
<body>
<header class="top-nav">
  <a class="wordmark" href="https://hassdns.com" target="_blank" rel="noopener">
    <img src="https://hassdns.com/android-chrome-192x192.png" alt="HassDNS">
    <span>Hass<b>DNS</b></span>
  </a>
  <button type="button" class="btn-back" onclick="goBackHA()" title="Volver a Home Assistant">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
    <span>Volver a Home Assistant</span>
  </button>
</header>
<main>
__BODY__
</main>
<footer class="foot">
  HassDNS · MavkSoft · <a href="https://hassdns.com/abuse.php" target="_blank" rel="noopener">Denunciar abuso</a> · <a href="https://hassdns.com/spec.php" target="_blank" rel="noopener">API</a> · <a href="https://hassdns.com/install.php" target="_blank" rel="noopener">Instalación</a> · <a href="https://hassdns.com/terminos.php" target="_blank" rel="noopener">Condiciones</a> · <a href="https://www.dynamicdnspro.com" target="_blank" rel="noopener">DynamicDNSPro</a>
</footer>
</body>
</html>"""

def page_logged(cfg):
    doms = cfg.get("domains", [])
    sel = set(cfg.get("selected") or [d["name"] for d in doms])
    if doms:
        rows = "".join(
            f'<label class="dom-row" style="cursor:pointer">'
            f'<input type="checkbox" name="dom" value="{d["name"]}"{" checked" if d["name"] in sel else ""} '
            f'style="accent-color:var(--accent,#22d3ee);width:16px;height:16px;flex:none">'
            f'<span class="dom-tag">{d.get("type","A")}</span><span class="dom-name">{d["name"]}</span>'
            f'<span class="dom-badge">{"✓ Activo" if d["name"] in sel else "Pausado"}</span></label>'
            for d in doms)
        rows = ('<form method="POST" action="select" style="margin-bottom:16px">' + rows +
                '<button type="submit" class="btn-primary" style="width:100%;margin-top:12px">Guardar selección</button></form>')
    else:
        rows = '<div class="mut" style="padding:12px 0;text-align:center;font-size:.9rem">Sin subdominios registrados aún. Créalos en <a href="https://hassdns.com/subdomains.php" target="_blank" rel="noopener">hassdns.com</a>.</div>'
    
    return f"""<div class="card">
  <div class="flash ok" style="display:flex;align-items:center;gap:8px">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
    <span><b>Sesión activa</b> — {len(sel)} de {len(doms)} dominio(s) en sincronización</span>
  </div>
  <h1 style="font-size:1.35rem;margin:12px 0 10px">Tus subdominios</h1>
  {rows}
  <p class="mut" style="font-size:.85rem;line-height:1.45;margin-bottom:20px">
    El add-on actualiza automáticamente la IP pública y gestiona la emisión y renovación del certificado SSL Let's Encrypt por DNS-01.
  </p>
  <div style="display:flex;gap:10px;flex-wrap:wrap">
    <button type="button" class="btn-primary" onclick="goBackHA()" style="flex:1">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
      <span>Volver a Home Assistant</span>
    </button>
    <form method="POST" action="logout" style="flex:none">
      <button type="submit" class="btn-bad" style="height:100%;padding:11px 16px">Cerrar sesión</button>
    </form>
  </div>
</div>"""

def page_login(err=""):
    flash = f'<div class="flash bad">{err}</div>' if err else ""
    return f"""<div class="card">
  <h1>Entra en HassDNS</h1>
  <p class="mut">Accede para gestionar tus subdominios y DNS dinámico en Home Assistant.</p>
  {flash}
  <form method="POST" action="login" class="stack">
    <label>Usuario o email
      <input type="text" name="u" autocomplete="username" required autofocus placeholder="Usuario o correo electrónico">
    </label>
    <label>Contraseña
      <input name="p" type="password" autocomplete="current-password" required placeholder="Tu contraseña">
    </label>
    <button type="submit" class="btn-primary">Entrar</button>
  </form>
  <p class="mut" style="margin-top:16px;text-align:center">
    <a href="https://hassdns.com/forgot.php" target="_blank" rel="noopener">¿Olvidaste tu contraseña?</a>
  </p>
  <p class="mut" style="margin-top:6px;text-align:center">
    ¿No tienes cuenta? <a href="https://hassdns.com/register.php" target="_blank" rel="noopener" style="font-weight:600">Crear cuenta gratis</a>
  </p>
  <details>
    <summary>¿Prefieres registrarte aquí mismo?</summary>
    <form method="POST" action="register" class="stack" style="margin-top:12px">
      <label>Email
        <input name="e" type="email" required autocomplete="email" placeholder="nombre@correo.com">
      </label>
      <label>Contraseña (mín. 8 caracteres)
        <input name="p2" type="password" required minlength="8" autocomplete="new-password">
      </label>
      <button type="submit" class="btn-secondary" style="margin-top:6px">Crear cuenta en HassDNS</button>
    </form>
  </details>
</div>"""

class H(http.server.BaseHTTPRequestHandler):
    def _send(self, body, code=200, ctype="text/html; charset=utf-8"):
        if isinstance(body, str): body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def _redirect(self, loc="."):
        # POST→Redirect→GET: sin POST en el historial no hay "¿reenviar formulario?".
        self.send_response(303)
        self.send_header("Location", loc)
        self.send_header("Content-Length", "0")
        self.end_headers()
    def log_message(self, *a): pass
    def _form(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 8192: return {}
        from urllib.parse import parse_qs
        return {k: v[0] for k, v in parse_qs(self.rfile.read(n).decode()).items()}
    def do_GET(self):
        p = self.path.split("?")[0]
        if p not in ("/", ""): return self._send(b"404 Not Found", 404, "text/plain")
        cfg = load_cfg()
        body = page_logged(cfg) if cfg.get("api_token") else page_login()
        self._send(PAGE.replace("__BODY__", body))
    def do_POST(self):
        p = self.path.split("?")[0]
        if p == "/select":
            n = int(self.headers.get("Content-Length") or 0)
            if n > 8192: n = 0
            from urllib.parse import parse_qs
            sel = parse_qs(self.rfile.read(n).decode() if n else "").get("dom", [])
            cfg = load_cfg()
            if sel:
                cfg["selected"] = sel
            else:
                cfg.pop("selected", None)
            save_cfg(cfg)
            apply_doms = sel if sel else [d["name"] for d in cfg.get("domains", [])]
            ha_apply(apply_doms, cfg.get("api_token", ""))
            return self._redirect()
        if p == "/logout":
            save_cfg({})
            ha_apply([], "")
            return self._redirect()
        if p == "/register":
            f = self._form()
            e, p2 = (f.get("e", "").strip().lower(), f.get("p2", ""))
            if not e or len(p2) < 8:
                return self._send(PAGE.replace("__BODY__", page_login("Email no válido o contraseña corta (mínimo 8 caracteres)")))
            r = api_register(e, p2)
            if not r.get("ok"):
                return self._send(PAGE.replace("__BODY__", page_login(r.get("error") or "No se pudo registrar la cuenta")))
            r2 = api_login(e, p2)
            if r2.get("ok"):
                save_cfg({"api_token": r2["api_token"], "domains": r2.get("domains", [])})
                ha_apply([d["name"] for d in r2.get("domains", [])], r2["api_token"])
                return self._redirect()
            return self._send(PAGE.replace("__BODY__", page_login("Cuenta creada correctamente — inicia sesión")))
        if p != "/login":
            return self._send(b"404 Not Found", 404, "text/plain")
        f = self._form()
        u, pw = (f.get("u", "").strip(), f.get("p", ""))
        if not u or not pw:
            return self._send(PAGE.replace("__BODY__", page_login("Por favor introduce usuario y contraseña")))
        r = api_login(u, pw)
        if not r.get("ok"):
            return self._send(PAGE.replace("__BODY__", page_login(r.get("error") or "Credenciales incorrectas")))
        save_cfg({"api_token": r["api_token"], "domains": r.get("domains", [])})
        ha_apply([d["name"] for d in r.get("domains", [])], r["api_token"])
        self._redirect()

if __name__ == "__main__":
    http.server.HTTPServer(("0.0.0.0", 8099), H).serve_forever()
