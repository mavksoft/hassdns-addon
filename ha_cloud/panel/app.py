#!/usr/bin/env python3
# HassDNS panel — mini-UI tras ingress de HA (la auth ya la hace HA).
# Seguridad: solo escucha el puerto de ingress (supervisor proxyfica y autentica),
# password NUNCA se persiste — solo el api_token resultante (config 600).
# Idioma: se detecta del Accept-Language del usuario de Home Assistant.
import json, os, ssl, urllib.request, urllib.error, http.server, secrets, subprocess, threading

DATA = "/data/panel_config.json" if os.path.exists("/data") else "/tmp/panel_config.json"
API  = "https://hassdns.com"
SUP       = "http://supervisor"
SUP_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")

# ── i18n ─────────────────────────────────────────────────────────────────────
STR = {
 "en": {"back":"Back to Home Assistant","login_title":"Sign in to HassDNS",
  "login_sub":"Sign in to manage your subdomains and dynamic DNS in Home Assistant.",
  "user_label":"Username or email","user_ph":"Username or email address","pass_label":"Password",
  "pass_ph":"Your password","signin":"Sign in","forgot":"Forgot your password?","no_account":"No account yet?",
  "create_free":"Create a free account","reg_here":"Prefer to sign up right here?","email_label":"Email",
  "email_ph":"name@email.com","pass_min":"Password (min. 8 characters)","create_acc":"Create HassDNS account",
  "err_badcreds":"Incorrect credentials","err_needcreds":"Please enter username and password",
  "err_email":"Invalid email or password too short (min. 8 characters)","err_reg":"Could not create the account",
  "reg_ok_login":"Account created — please sign in","session_active":"Active session",
  "insync":"{n} of {m} domain(s) syncing","your_subs":"Your subdomains","active":"Active","paused":"Paused",
  "no_subs":"No subdomains yet. Create them at","save_sel":"Save selection",
  "addon_desc":"The add-on automatically updates your public IP and handles issuing and renewing the Let's Encrypt SSL certificate via DNS-01.",
  "logout":"Sign out","saved_title":"Settings saved","saved_msg":"Returning to Home Assistant…","return_now":"Return now",
  "foot_abuse":"Report abuse","foot_install":"Install","foot_terms":"Terms"},
 "es": {"back":"Volver a Home Assistant","login_title":"Entra en HassDNS",
  "login_sub":"Accede para gestionar tus subdominios y DNS dinámico en Home Assistant.",
  "user_label":"Usuario o email","user_ph":"Usuario o correo electrónico","pass_label":"Contraseña",
  "pass_ph":"Tu contraseña","signin":"Entrar","forgot":"¿Olvidaste tu contraseña?","no_account":"¿No tienes cuenta?",
  "create_free":"Crear cuenta gratis","reg_here":"¿Prefieres registrarte aquí mismo?","email_label":"Email",
  "email_ph":"nombre@correo.com","pass_min":"Contraseña (mín. 8 caracteres)","create_acc":"Crear cuenta en HassDNS",
  "err_badcreds":"Credenciales incorrectas","err_needcreds":"Por favor introduce usuario y contraseña",
  "err_email":"Email no válido o contraseña corta (mínimo 8 caracteres)","err_reg":"No se pudo crear la cuenta",
  "reg_ok_login":"Cuenta creada — inicia sesión","session_active":"Sesión activa",
  "insync":"{n} de {m} dominio(s) en sincronización","your_subs":"Tus subdominios","active":"Activo","paused":"Pausado",
  "no_subs":"Aún no tienes subdominios. Créalos en","save_sel":"Guardar selección",
  "addon_desc":"El add-on actualiza automáticamente la IP pública y gestiona la emisión y renovación del certificado SSL Let's Encrypt por DNS-01.",
  "logout":"Cerrar sesión","saved_title":"Configuración guardada","saved_msg":"Volviendo a Home Assistant…","return_now":"Volver ahora",
  "foot_abuse":"Denunciar abuso","foot_install":"Instalación","foot_terms":"Condiciones"},
 "de": {"back":"Zurück zu Home Assistant","login_title":"Bei HassDNS anmelden",
  "login_sub":"Melde dich an, um deine Subdomains und dynamisches DNS in Home Assistant zu verwalten.",
  "user_label":"Benutzername oder E-Mail","user_ph":"Benutzername oder E-Mail-Adresse","pass_label":"Passwort",
  "pass_ph":"Dein Passwort","signin":"Anmelden","forgot":"Passwort vergessen?","no_account":"Noch kein Konto?",
  "create_free":"Kostenloses Konto erstellen","reg_here":"Lieber direkt hier registrieren?","email_label":"E-Mail",
  "email_ph":"name@mail.com","pass_min":"Passwort (mind. 8 Zeichen)","create_acc":"HassDNS-Konto erstellen",
  "err_badcreds":"Ungültige Anmeldedaten","err_needcreds":"Bitte Benutzername und Passwort eingeben",
  "err_email":"Ungültige E-Mail oder Passwort zu kurz (mind. 8 Zeichen)","err_reg":"Konto konnte nicht erstellt werden",
  "reg_ok_login":"Konto erstellt — bitte anmelden","session_active":"Sitzung aktiv",
  "insync":"{n} von {m} Domain(s) werden synchronisiert","your_subs":"Deine Subdomains","active":"Aktiv","paused":"Pausiert",
  "no_subs":"Noch keine Subdomains. Erstelle sie auf","save_sel":"Auswahl speichern",
  "addon_desc":"Das Add-on aktualisiert automatisch deine öffentliche IP und kümmert sich um Ausstellung und Erneuerung des Let's-Encrypt-SSL-Zertifikats per DNS-01.",
  "logout":"Abmelden","saved_title":"Einstellungen gespeichert","saved_msg":"Zurück zu Home Assistant…","return_now":"Jetzt zurück",
  "foot_abuse":"Missbrauch melden","foot_install":"Installation","foot_terms":"Bedingungen"},
 "fr": {"back":"Retour à Home Assistant","login_title":"Connexion à HassDNS",
  "login_sub":"Connectez-vous pour gérer vos sous-domaines et le DNS dynamique dans Home Assistant.",
  "user_label":"Nom d'utilisateur ou e-mail","user_ph":"Nom d'utilisateur ou adresse e-mail","pass_label":"Mot de passe",
  "pass_ph":"Votre mot de passe","signin":"Se connecter","forgot":"Mot de passe oublié ?","no_account":"Pas encore de compte ?",
  "create_free":"Créer un compte gratuit","reg_here":"Vous préférez vous inscrire ici ?","email_label":"E-mail",
  "email_ph":"nom@mail.com","pass_min":"Mot de passe (min. 8 caractères)","create_acc":"Créer un compte HassDNS",
  "err_badcreds":"Identifiants incorrects","err_needcreds":"Veuillez saisir l'utilisateur et le mot de passe",
  "err_email":"E-mail invalide ou mot de passe trop court (min. 8 caractères)","err_reg":"Impossible de créer le compte",
  "reg_ok_login":"Compte créé — connectez-vous","session_active":"Session active",
  "insync":"{n} domaine(s) sur {m} en synchronisation","your_subs":"Vos sous-domaines","active":"Actif","paused":"En pause",
  "no_subs":"Aucun sous-domaine pour l'instant. Créez-les sur","save_sel":"Enregistrer la sélection",
  "addon_desc":"L'add-on met à jour automatiquement votre IP publique et gère l'émission et le renouvellement du certificat SSL Let's Encrypt via DNS-01.",
  "logout":"Se déconnecter","saved_title":"Configuration enregistrée","saved_msg":"Retour à Home Assistant…","return_now":"Revenir maintenant",
  "foot_abuse":"Signaler un abus","foot_install":"Installation","foot_terms":"Conditions"},
 "it": {"back":"Torna a Home Assistant","login_title":"Accedi a HassDNS",
  "login_sub":"Accedi per gestire i tuoi sottodomini e il DNS dinamico in Home Assistant.",
  "user_label":"Nome utente o email","user_ph":"Nome utente o indirizzo email","pass_label":"Password",
  "pass_ph":"La tua password","signin":"Accedi","forgot":"Password dimenticata?","no_account":"Non hai un account?",
  "create_free":"Crea un account gratuito","reg_here":"Preferisci registrarti qui?","email_label":"Email",
  "email_ph":"nome@mail.com","pass_min":"Password (min. 8 caratteri)","create_acc":"Crea account HassDNS",
  "err_badcreds":"Credenziali errate","err_needcreds":"Inserisci nome utente e password",
  "err_email":"Email non valida o password troppo corta (min. 8 caratteri)","err_reg":"Impossibile creare l'account",
  "reg_ok_login":"Account creato — accedi","session_active":"Sessione attiva",
  "insync":"{n} di {m} dominio/i in sincronizzazione","your_subs":"I tuoi sottodomini","active":"Attivo","paused":"In pausa",
  "no_subs":"Ancora nessun sottodominio. Creali su","save_sel":"Salva selezione",
  "addon_desc":"L'add-on aggiorna automaticamente il tuo IP pubblico e gestisce l'emissione e il rinnovo del certificato SSL Let's Encrypt tramite DNS-01.",
  "logout":"Esci","saved_title":"Impostazioni salvate","saved_msg":"Ritorno a Home Assistant…","return_now":"Torna ora",
  "foot_abuse":"Segnala abuso","foot_install":"Installazione","foot_terms":"Condizioni"},
 "pt": {"back":"Voltar ao Home Assistant","login_title":"Entrar no HassDNS",
  "login_sub":"Entre para gerir os seus subdomínios e DNS dinâmico no Home Assistant.",
  "user_label":"Utilizador ou email","user_ph":"Utilizador ou endereço de email","pass_label":"Palavra-passe",
  "pass_ph":"A sua palavra-passe","signin":"Entrar","forgot":"Esqueceu a palavra-passe?","no_account":"Ainda não tem conta?",
  "create_free":"Criar conta grátis","reg_here":"Prefere registar-se aqui?","email_label":"Email",
  "email_ph":"nome@mail.com","pass_min":"Palavra-passe (mín. 8 caracteres)","create_acc":"Criar conta HassDNS",
  "err_badcreds":"Credenciais incorretas","err_needcreds":"Introduza utilizador e palavra-passe",
  "err_email":"Email inválido ou palavra-passe curta (mín. 8 caracteres)","err_reg":"Não foi possível criar a conta",
  "reg_ok_login":"Conta criada — inicie sessão","session_active":"Sessão ativa",
  "insync":"{n} de {m} domínio(s) a sincronizar","your_subs":"Os seus subdomínios","active":"Ativo","paused":"Em pausa",
  "no_subs":"Ainda sem subdomínios. Crie-os em","save_sel":"Guardar seleção",
  "addon_desc":"O add-on atualiza automaticamente o seu IP público e trata da emissão e renovação do certificado SSL Let's Encrypt via DNS-01.",
  "logout":"Terminar sessão","saved_title":"Configuração guardada","saved_msg":"A voltar ao Home Assistant…","return_now":"Voltar agora",
  "foot_abuse":"Denunciar abuso","foot_install":"Instalação","foot_terms":"Condições"},
}

def pick_lang(accept):
    for part in (accept or "").split(","):
        code = part.split(";")[0].strip().lower().replace("_", "-")[:2]
        if code in STR:
            return code
    return "en"

def t(lang, key):
    return STR.get(lang, STR["en"]).get(key, STR["en"].get(key, key))

# ── estado + Supervisor API ──────────────────────────────────────────────────
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
        raise RuntimeError("HTTP %s: %s" % (e.code, e.read().decode(errors="replace")[:300]))

def _restart():
    try:
        _sup("POST", "/addons/self/restart"); _log("reinicio del add-on solicitado")
    except Exception as e:
        _log("reinicio FALLO:", e)

def ha_apply(domains, token):
    # Escribe domains/token en las OPCIONES del add-on (pestaña Configuración) y
    # reinicia para aplicarlas: fuente única = opciones del add-on.
    if not SUP_TOKEN:
        _log("ha_apply: NO hay SUPERVISOR_TOKEN (¿falta hassio_api, o add-on sin actualizar?)")
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
    threading.Timer(3.0, _restart).start()
    return True

def api_register(email, pw):
    req = urllib.request.Request(API + "/api_register.php",
        data=json.dumps({"email": email, "password": pw}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def api_login(user, pw):
    req = urllib.request.Request(API + "/api_login.php",
        data=json.dumps({"user": user, "pass": pw}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

# ── plantilla (placeholders, no f-string: el CSS tiene llaves) ────────────────
PAGE = """<!doctype html>
<html lang="__LANG__">
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
  display:flex;flex-direction:column;justify-content:space-between;align-items:center;padding:16px 20px;
}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.top-nav{width:100%;max-width:960px;display:flex;align-items:center;justify-content:space-between;padding:8px 0 16px;gap:12px}
.wordmark{display:flex;align-items:center;gap:10px;font-weight:700;font-size:1.15rem;letter-spacing:-.01em;color:var(--ink);text-decoration:none}
.wordmark img{width:32px;height:32px;border-radius:7px;display:block}
.wordmark span b{color:var(--accent);font-weight:700}
.btn-back{
  display:inline-flex;align-items:center;gap:8px;background:rgba(24,33,40,0.85);color:var(--muted);
  border:1px solid rgba(255,255,255,0.08);border-radius:999px;padding:8px 16px;
  font:600 .88rem 'General Sans',sans-serif;cursor:pointer;transition:all .18s ease;
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);text-decoration:none;
}
.btn-back:hover{background:rgba(34,211,238,0.15);color:var(--accent);border-color:rgba(34,211,238,0.35);transform:translateX(-2px);text-decoration:none}
main{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;width:100%;padding:16px 0}
.card{
  width:100%;max-width:440px;background:rgba(19,26,31,0.92);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  border:1px solid rgba(255,255,255,0.08);box-shadow:0 16px 48px rgba(0,0,0,0.55);border-radius:14px;padding:28px 24px;box-sizing:border-box;
}
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
input:-webkit-autofill,input:-webkit-autofill:hover,input:-webkit-autofill:focus,input:-webkit-autofill:active{
  -webkit-box-shadow:0 0 0 1000px #07090e inset !important;-webkit-text-fill-color:#f4f7f8 !important;
  caret-color:#f4f7f8 !important;transition:background-color 5000s ease-in-out 0s;
}
button.btn-primary{
  display:inline-flex;align-items:center;justify-content:center;gap:8px;background:var(--accent);color:var(--accent-ink);
  border:0;border-radius:var(--radius);padding:12px 20px;font:700 .95rem 'General Sans',sans-serif;cursor:pointer;
  transition:transform .18s,background .18s;width:100%;margin-top:6px;
}
button.btn-primary:hover{background:#38e1fc;transform:translateY(-1px)}
button.btn-secondary{
  display:inline-flex;align-items:center;justify-content:center;gap:8px;background:var(--surface-2);color:var(--ink);
  border:1px solid var(--line);border-radius:var(--radius);padding:10px 18px;font:600 .9rem 'General Sans',sans-serif;cursor:pointer;transition:background .18s;width:100%;
}
button.btn-secondary:hover{background:#223039}
button.btn-bad{
  display:inline-flex;align-items:center;justify-content:center;background:transparent;color:var(--bad);
  border:1px solid rgba(248,113,113,0.3);border-radius:8px;padding:9px 16px;font:600 .85rem 'General Sans',sans-serif;cursor:pointer;transition:all .18s;
}
button.btn-bad:hover{background:rgba(248,113,113,0.12)}
.dom-row{display:flex;flex-direction:row;align-items:center;gap:10px;padding:10px 12px;background:var(--bg);border:1px solid var(--line);border-radius:8px;margin-bottom:8px}
.dom-tag{background:var(--surface-2);color:var(--accent);border:1px solid rgba(34,211,238,0.25);padding:2px 8px;border-radius:6px;font-size:.75rem;font-weight:700}
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
function goBackHA(){
  try{ if(window.parent&&window.parent!==window){window.parent.history.back();return;} }catch(e){}
  try{ if(window.top&&window.top!==window){window.top.history.back();return;} }catch(e){}
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
  <button type="button" class="btn-back" onclick="goBackHA()" title="__BACK__">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
    <span>__BACK__</span>
  </button>
</header>
<main>
__BODY__
</main>
<footer class="foot">
  HassDNS · MavkSoft · <a href="https://hassdns.com/abuse.php" target="_blank" rel="noopener">__FOOT_ABUSE__</a> · <a href="https://hassdns.com/spec.php" target="_blank" rel="noopener">API</a> · <a href="https://hassdns.com/install.php" target="_blank" rel="noopener">__FOOT_INSTALL__</a> · <a href="https://hassdns.com/terminos.php" target="_blank" rel="noopener">__FOOT_TERMS__</a> · <a href="https://www.dynamicdnspro.com" target="_blank" rel="noopener">DynamicDNSPro</a>
</footer>
</body>
</html>"""

def shell(body, lang):
    return (PAGE.replace("__LANG__", lang)
                .replace("__BACK__", t(lang, "back"))
                .replace("__FOOT_ABUSE__", t(lang, "foot_abuse"))
                .replace("__FOOT_INSTALL__", t(lang, "foot_install"))
                .replace("__FOOT_TERMS__", t(lang, "foot_terms"))
                .replace("__BODY__", body))

def page_logged(cfg, lang):
    doms = cfg.get("domains", [])
    sel = set(cfg.get("selected") or [d["name"] for d in doms])
    if doms:
        rows = "".join(
            f'<label class="dom-row" style="cursor:pointer">'
            f'<input type="checkbox" name="dom" value="{d["name"]}"{" checked" if d["name"] in sel else ""} '
            f'style="accent-color:var(--accent,#22d3ee);width:16px;height:16px;flex:none">'
            f'<span class="dom-tag">{d.get("type","A")}</span><span class="dom-name">{d["name"]}</span>'
            f'<span class="dom-badge">{("✓ "+t(lang,"active")) if d["name"] in sel else t(lang,"paused")}</span></label>'
            for d in doms)
        rows = ('<form method="POST" action="select" style="margin-bottom:16px">' + rows +
                f'<button type="submit" class="btn-primary" style="width:100%;margin-top:12px">{t(lang,"save_sel")}</button></form>')
    else:
        rows = (f'<div class="mut" style="padding:12px 0;text-align:center;font-size:.9rem">{t(lang,"no_subs")} '
                '<a href="https://hassdns.com/subdomains.php" target="_blank" rel="noopener">hassdns.com</a>.</div>')
    return f"""<div class="card">
  <div class="flash ok" style="display:flex;align-items:center;gap:8px">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
    <span><b>{t(lang,"session_active")}</b> — {t(lang,"insync").format(n=len(sel), m=len(doms))}</span>
  </div>
  <h1 style="font-size:1.35rem;margin:4px 0 10px">{t(lang,"your_subs")}</h1>
  {rows}
  <p class="mut" style="font-size:.85rem;line-height:1.45;margin-bottom:20px">{t(lang,"addon_desc")}</p>
  <div style="display:flex;justify-content:flex-end">
    <form method="POST" action="logout">
      <button type="submit" class="btn-bad" style="padding:10px 18px">{t(lang,"logout")}</button>
    </form>
  </div>
</div>"""

def page_login(err, lang):
    flash = f'<div class="flash bad">{err}</div>' if err else ""
    return f"""<div class="card">
  <h1>{t(lang,"login_title")}</h1>
  <p class="mut">{t(lang,"login_sub")}</p>
  {flash}
  <form method="POST" action="login" class="stack">
    <label>{t(lang,"user_label")}
      <input type="text" name="u" autocomplete="username" required autofocus placeholder="{t(lang,'user_ph')}">
    </label>
    <label>{t(lang,"pass_label")}
      <input name="p" type="password" autocomplete="current-password" required placeholder="{t(lang,'pass_ph')}">
    </label>
    <button type="submit" class="btn-primary">{t(lang,"signin")}</button>
  </form>
  <p class="mut" style="margin-top:16px;text-align:center">
    <a href="https://hassdns.com/forgot.php" target="_blank" rel="noopener">{t(lang,"forgot")}</a>
  </p>
  <p class="mut" style="margin-top:6px;text-align:center">
    {t(lang,"no_account")} <a href="https://hassdns.com/register.php" target="_blank" rel="noopener" style="font-weight:600">{t(lang,"create_free")}</a>
  </p>
  <details>
    <summary>{t(lang,"reg_here")}</summary>
    <form method="POST" action="register" class="stack" style="margin-top:12px">
      <label>{t(lang,"email_label")}
        <input name="e" type="email" required autocomplete="email" placeholder="{t(lang,'email_ph')}">
      </label>
      <label>{t(lang,"pass_min")}
        <input name="p2" type="password" required minlength="8" autocomplete="new-password">
      </label>
      <button type="submit" class="btn-secondary" style="margin-top:6px">{t(lang,"create_acc")}</button>
    </form>
  </details>
</div>"""

def page_saved(lang):
    # Tras guardar: confirmación + retorno automático a HA (y un "Volver ahora").
    return f"""<div class="card" style="text-align:center">
  <div style="width:56px;height:56px;margin:4px auto 14px;border-radius:50%;background:rgba(45,212,191,0.14);display:flex;align-items:center;justify-content:center">
    <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="var(--ok)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
  </div>
  <h1 style="font-size:1.3rem">{t(lang,"saved_title")}</h1>
  <p class="mut" style="margin-top:8px">{t(lang,"saved_msg")}</p>
  <button type="button" class="btn-primary" onclick="goBackHA()" style="margin-top:12px">{t(lang,"return_now")}</button>
</div>
<script>
  try{{history.replaceState(null,'','.');}}catch(e){{}}
  setTimeout(goBackHA, 2500);
</script>"""

class H(http.server.BaseHTTPRequestHandler):
    def _lang(self):
        return pick_lang(self.headers.get("Accept-Language", ""))
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
        from urllib.parse import urlparse, parse_qs
        lang = self._lang()
        u = urlparse(self.path)
        if u.path not in ("/", ""): return self._send(b"404 Not Found", 404, "text/plain")
        if parse_qs(u.query).get("saved"):
            return self._send(shell(page_saved(lang), lang))
        cfg = load_cfg()
        body = page_logged(cfg, lang) if cfg.get("api_token") else page_login("", lang)
        self._send(shell(body, lang))
    def do_POST(self):
        lang = self._lang()
        p = self.path.split("?")[0]
        if p == "/select":
            from urllib.parse import parse_qs
            n = int(self.headers.get("Content-Length") or 0)
            if n > 8192: n = 0
            sel = parse_qs(self.rfile.read(n).decode() if n else "").get("dom", [])
            cfg = load_cfg()
            if sel: cfg["selected"] = sel
            else:   cfg.pop("selected", None)
            save_cfg(cfg)
            apply_doms = sel if sel else [d["name"] for d in cfg.get("domains", [])]
            ha_apply(apply_doms, cfg.get("api_token", ""))
            return self._redirect("./?saved=1")
        if p == "/logout":
            save_cfg({})
            ha_apply([], "")
            return self._redirect(".")
        if p == "/register":
            f = self._form()
            e, p2 = (f.get("e", "").strip().lower(), f.get("p2", ""))
            if not e or len(p2) < 8:
                return self._send(shell(page_login(t(lang, "err_email"), lang), lang))
            r = api_register(e, p2)
            if not r.get("ok"):
                return self._send(shell(page_login(r.get("error") or t(lang, "err_reg"), lang), lang))
            r2 = api_login(e, p2)
            if r2.get("ok"):
                save_cfg({"api_token": r2["api_token"], "domains": r2.get("domains", [])})
                return self._redirect(".")
            return self._send(shell(page_login(t(lang, "reg_ok_login"), lang), lang))
        if p != "/login":
            return self._send(b"404 Not Found", 404, "text/plain")
        f = self._form()
        u, pw = (f.get("u", "").strip(), f.get("p", ""))
        if not u or not pw:
            return self._send(shell(page_login(t(lang, "err_needcreds"), lang), lang))
        r = api_login(u, pw)
        if not r.get("ok"):
            return self._send(shell(page_login(r.get("error") or t(lang, "err_badcreds"), lang), lang))
        save_cfg({"api_token": r["api_token"], "domains": r.get("domains", [])})
        self._redirect(".")

if __name__ == "__main__":
    http.server.HTTPServer(("0.0.0.0", 8099), H).serve_forever()
