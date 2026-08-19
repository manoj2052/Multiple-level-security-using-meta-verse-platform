"""
PHASE 1 — VULNERABLE METAVERSE PLATFORM
========================================
INTENTIONAL VULNERABILITIES (for demo):
  [V1] SQL Injection in /login — raw f-string query
  [V2] No rate limiting — Hydra can brute-force freely
  [V3] Weak JWT secret ('secret') — easily cracked
  [V4] JWT token exposed in URL param /api/user?token=
  [V5] debug=True — Werkzeug debugger exposes stack traces
  [V6] No CSRF protection
  [V7] Passwords stored as plain SHA-256 (no salt)
"""

from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
import sqlite3, hashlib, jwt, datetime, os

app = Flask(__name__)
app.secret_key = 'secret123'          # [V3] Weak secret
JWT_SECRET   = 'secret'               # [V3] Easily crackable

# ─────────────────────── HTML TEMPLATES ───────────────────────

BASE_STYLE = """
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#080d1a;--bg2:#0d1426;--bg3:#121c35;--blue:#00d4ff;--green:#00ff88;--red:#ff3860;--amber:#ffb800;--text:#c8d6f0;--text2:#7a92c8;--border:#1e2d55}
body{background:var(--bg);color:var(--text);font-family:'Rajdhani',sans-serif;min-height:100vh}
a{color:var(--blue);text-decoration:none}
input,select,button{font-family:'Rajdhani',sans-serif}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:28px}
.btn{display:inline-block;padding:11px 24px;border-radius:7px;border:none;cursor:pointer;font-size:15px;font-weight:700;letter-spacing:1px;transition:all .25s}
.btn-blue{background:rgba(0,212,255,.12);color:var(--blue);border:1px solid rgba(0,212,255,.4)}
.btn-blue:hover{background:rgba(0,212,255,.25)}
.btn-red{background:rgba(255,56,96,.12);color:var(--red);border:1px solid rgba(255,56,96,.4)}
.btn-green{background:rgba(0,255,136,.1);color:var(--green);border:1px solid rgba(0,255,136,.3)}
.inp{width:100%;padding:12px 14px;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:7px;color:var(--text);font-size:15px;margin:6px 0 16px}
.inp:focus{outline:none;border-color:var(--blue)}
label{font-size:13px;color:var(--text2);letter-spacing:1px;text-transform:uppercase}
.error{color:var(--red);background:rgba(255,56,96,.08);border:1px solid rgba(255,56,96,.3);border-radius:6px;padding:10px 14px;margin-bottom:16px;font-size:14px}
.tag{font-size:10px;padding:3px 8px;border-radius:4px;font-weight:700;letter-spacing:1px;text-transform:uppercase}
.tag-nft{background:rgba(180,79,255,.2);color:#b44fff;border:1px solid rgba(180,79,255,.3)}
.tag-land{background:rgba(0,212,255,.1);color:var(--blue);border:1px solid rgba(0,212,255,.25)}
.tag-coin{background:rgba(255,184,0,.1);color:var(--amber);border:1px solid rgba(255,184,0,.25)}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-thumb{background:#1e2d55;border-radius:2px}
</style>
"""

INDEX_HTML = BASE_STYLE + """
<title>MetaVerse — Enter the Digital World</title>
<style>
.hero{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:40px;background:radial-gradient(ellipse at 50% 0%,rgba(0,212,255,.08) 0%,transparent 70%)}
.logo{font-family:'Orbitron',monospace;font-size:52px;font-weight:900;color:var(--blue);text-shadow:0 0 40px rgba(0,212,255,.5);margin-bottom:12px}
.logo span{color:var(--green)}
.tagline{font-size:20px;color:var(--text2);margin-bottom:48px;letter-spacing:2px}
.btn-row{display:flex;gap:16px;justify-content:center}
.features{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:900px;margin:60px auto 0}
.feat{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:24px;text-align:center}
.feat .icon{font-size:32px;margin-bottom:12px}
.feat h3{font-family:'Orbitron',monospace;font-size:13px;color:var(--blue);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px}
.feat p{font-size:14px;color:var(--text2);line-height:1.6}
.vuln-bar{position:fixed;bottom:0;left:0;right:0;background:rgba(255,56,96,.1);border-top:1px solid rgba(255,56,96,.3);padding:8px 20px;font-family:'Share Tech Mono',monospace;font-size:11px;color:var(--red);text-align:center}
</style>
<div class="hero">
  <div class="logo">META<span>VERSE</span></div>
  <div class="tagline">Your Digital Identity. Your Virtual World.</div>
  <div class="btn-row">
    <a href="/login" class="btn btn-blue">Enter MetaVerse</a>
    <a href="/register" class="btn btn-green">Create Identity</a>
  </div>
  <div class="features">
    <div class="feat"><div class="icon">🧑‍💻</div><h3>Digital Identity</h3><p>Create your unique avatar and build your presence in the virtual world</p></div>
    <div class="feat"><div class="icon">💎</div><h3>NFT Assets</h3><p>Own, trade, and display digital assets secured by blockchain hashing</p></div>
    <div class="feat"><div class="icon">🌐</div><h3>Virtual Economy</h3><p>Transact with MetaCoins in a fully digital peer-to-peer economy</p></div>
  </div>
</div>
<div class="vuln-bar">⚠ PHASE 1 — VULNERABLE MODE | SHA-256 Auth | JWT Active | No Rate Limiting | SQL Injection Possible</div>
"""

LOGIN_HTML = BASE_STYLE + """
<title>Login — MetaVerse</title>
<style>
.center{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.login-box{width:100%;max-width:420px}
.logo{font-family:'Orbitron',monospace;font-size:26px;color:var(--blue);margin-bottom:4px;font-weight:900}
.sub{font-size:13px;color:var(--text2);margin-bottom:28px;letter-spacing:1px}
.vuln-note{background:rgba(255,56,96,.06);border:1px solid rgba(255,56,96,.2);border-radius:6px;padding:10px 14px;margin-bottom:20px;font-size:12px;color:var(--red);font-family:'Share Tech Mono',monospace}
</style>
<div class="center">
  <div class="login-box">
    <div class="logo">METAVERSE</div>
    <div class="sub">Authenticate to enter the virtual world</div>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <div class="card">
      <div class="vuln-note">⚠ [V1] No brute-force protection &nbsp;|&nbsp; [V2] SQL Injectable</div>
      <form method="POST">
        <label>User ID</label>
        <input class="inp" type="text" name="username" placeholder="Enter your username" required>
        <label>Password</label>
        <input class="inp" type="password" name="password" placeholder="Enter your password" required>
        <button class="btn btn-blue" style="width:100%;padding:14px;font-size:16px" type="submit">ENTER METAVERSE →</button>
      </form>
      <div style="text-align:center;margin-top:20px;font-size:14px;color:var(--text2)">
        No identity? <a href="/register">Create one</a>
      </div>
    </div>
    <div style="text-align:center;margin-top:20px;font-size:12px;color:#3a4a6a">
      🔴 Vulnerable: try username: <code style="color:var(--red)">alice' OR '1'='1' --</code>
    </div>
  </div>
</div>
"""

REGISTER_HTML = BASE_STYLE + """
<title>Register — MetaVerse</title>
<style>
.center{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.box{width:100%;max-width:420px}
.logo{font-family:'Orbitron',monospace;font-size:26px;color:var(--green);margin-bottom:4px;font-weight:900}
.sub{font-size:13px;color:var(--text2);margin-bottom:28px;letter-spacing:1px}
.hash-note{font-family:'Share Tech Mono',monospace;font-size:11px;color:var(--text2);background:var(--bg3);padding:10px;border-radius:6px;margin-bottom:16px;word-break:break-all}
</style>
<div class="center">
  <div class="box">
    <div class="logo">CREATE IDENTITY</div>
    <div class="sub">SHA-256 secured registration</div>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <div class="card">
      <form method="POST" id="reg-form">
        <label>Username</label>
        <input class="inp" type="text" name="username" id="uname" placeholder="Choose your avatar name" required>
        <label>Email</label>
        <input class="inp" type="email" name="email" placeholder="your@email.com" required>
        <label>Password</label>
        <input class="inp" type="password" name="password" id="pw" placeholder="Set your password" oninput="showHash()" required>
        <div class="hash-note" id="hash-display">SHA-256 hash will appear here...</div>
        <button class="btn btn-green" style="width:100%;padding:14px;font-size:16px" type="submit">REGISTER IDENTITY →</button>
      </form>
      <div style="text-align:center;margin-top:16px;font-size:14px;color:var(--text2)">
        Already registered? <a href="/login">Login</a>
      </div>
    </div>
  </div>
</div>
<script>
async function showHash(){
  const pw = document.getElementById('pw').value;
  if(!pw){document.getElementById('hash-display').textContent='SHA-256 hash will appear here...';return;}
  const enc = new TextEncoder().encode(pw);
  const buf = await crypto.subtle.digest('SHA-256', enc);
  const hex = Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('');
  document.getElementById('hash-display').textContent = 'SHA-256: ' + hex;
}
</script>
"""

DASHBOARD_HTML = BASE_STYLE + """
<title>MetaVerse — Dashboard</title>
<style>
.navbar{background:var(--bg2);border-bottom:1px solid var(--border);padding:14px 32px;display:flex;align-items:center;justify-content:space-between}
.nav-logo{font-family:'Orbitron',monospace;font-size:18px;color:var(--blue);font-weight:900}
.nav-user{display:flex;align-items:center;gap:16px;font-size:14px}
.avatar-circle{width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,var(--blue),var(--green));display:flex;align-items:center;justify-content:center;font-weight:900;font-size:16px;color:#000}
.main{max-width:1200px;margin:0 auto;padding:28px 24px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-bottom:24px}
.stat{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:18px 20px}
.stat .num{font-family:'Orbitron',monospace;font-size:26px;font-weight:700;margin-bottom:4px}
.stat .lbl{font-size:12px;color:var(--text2);letter-spacing:1px;text-transform:uppercase}
.grid2{display:grid;grid-template-columns:2fr 1fr;gap:20px}
.section-title{font-family:'Orbitron',monospace;font-size:12px;color:var(--blue);letter-spacing:2px;text-transform:uppercase;margin-bottom:14px}
.asset-card{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;margin-bottom:10px}
.asset-name{font-size:15px;font-weight:600;margin-bottom:3px}
.asset-val{font-family:'Orbitron',monospace;font-size:13px;color:var(--green)}
.log-entry{padding:10px 14px;background:var(--bg3);border-left:3px solid var(--border);border-radius:4px;margin-bottom:8px;font-family:'Share Tech Mono',monospace;font-size:12px}
.log-entry.login{border-left-color:var(--green)}
.log-entry.fail{border-left-color:var(--red)}
.log-entry.transfer{border-left-color:var(--amber)}
.tx-input{display:flex;gap:10px;margin-bottom:10px}
.tx-input input{flex:1;padding:10px 12px;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:14px}
.jwt-box{background:#060b15;border:1px solid var(--border);border-radius:6px;padding:12px;font-family:'Share Tech Mono',monospace;font-size:10px;color:var(--amber);word-break:break-all;margin-top:10px}
.vuln-bar{background:rgba(255,56,96,.06);border:1px solid rgba(255,56,96,.2);border-radius:6px;padding:10px 16px;margin-bottom:20px;font-size:12px;color:var(--red);font-family:'Share Tech Mono',monospace}
</style>
<div class="navbar">
  <div class="nav-logo">METAVERSE</div>
  <div class="nav-user">
    <div class="avatar-circle">{{ user['username'][0]|upper }}</div>
    <div><div style="font-weight:700">{{ user['username'] }}</div><div style="font-size:11px;color:var(--text2)">ID: #{{ user['id'] }}</div></div>
    <a href="/logout" class="btn btn-red" style="padding:7px 16px;font-size:13px">Logout</a>
  </div>
</div>
<div class="main">
  <div class="vuln-bar">⚠ [V3] JWT Token (weak secret 'secret'): {{ token[:60] }}... &nbsp;|&nbsp; <a href="/api/user?token={{ token }}" style="color:var(--amber)">[V4] Token exposed in URL</a></div>
  <div class="grid3">
    <div class="stat"><div class="num" style="color:var(--green)">{{ '%.2f'|format(wallet['balance']) }} MC</div><div class="lbl">MetaCoin Balance</div></div>
    <div class="stat"><div class="num" style="color:var(--blue)">{{ assets|length }}</div><div class="lbl">Digital Assets</div></div>
    <div class="stat"><div class="num" style="color:var(--amber)">{{ '%.2f'|format(assets|sum(attribute='value')) }} MC</div><div class="lbl">Portfolio Value</div></div>
  </div>
  <div class="grid2">
    <div>
      <div class="card" style="margin-bottom:20px">
        <div class="section-title">Digital Assets</div>
        {% for asset in assets %}
        <div class="asset-card">
          <div>
            <div class="asset-name">{{ asset['name'] }}</div>
            <span class="tag tag-{{ asset['type']|lower }}">{{ asset['type'] }}</span>
          </div>
          <div class="asset-val">{{ '%.2f'|format(asset['value']) }} MC</div>
        </div>
        {% endfor %}
      </div>
      <div class="card">
        <div class="section-title">Transfer MetaCoins</div>
        <form method="POST" action="/transfer">
          <div class="tx-input">
            <input type="text" name="to_user" placeholder="Recipient username">
            <input type="number" name="amount" placeholder="Amount" step="0.01" min="0.01">
          </div>
          <button class="btn btn-green" type="submit">Send →</button>
        </form>
        <div style="margin-top:14px;font-size:12px;color:var(--text2)">
          Transactions secured with SHA-256 hashing
        </div>
        <div class="jwt-box">{{ tx_hash }}</div>
      </div>
    </div>
    <div>
      <div class="card">
        <div class="section-title">Activity Log</div>
        {% for log in logs %}
        <div class="log-entry {{ 'login' if 'LOGIN' in log['action'] else ('fail' if 'FAIL' in log['action'] else 'transfer') }}">
          <div style="color:var(--text2)">{{ log['timestamp'][:16] }}</div>
          <div>{{ log['action'] }} — {{ log['ip_address'] }}</div>
          <div style="color:var(--text2)">{{ log['details'] }}</div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>
"""

# ─────────────────────── DATABASE ───────────────────────

def get_db():
    conn = sqlite3.connect('metaverse.db')
    conn.row_factory = sqlite3.Row
    return conn

def log_activity(user_id, action, ip, details):
    conn = get_db()
    conn.execute(
        'INSERT INTO activity_logs (user_id, action, ip_address, details, timestamp) VALUES (?,?,?,?,?)',
        (user_id, action, ip, details, datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def hash_password(password):
    # [V7] No salt — vulnerable to rainbow table attacks
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id, username):
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

# ─────────────────────── ROUTES ───────────────────────

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed   = hash_password(password)
        conn     = get_db()

        # ════════════════════════════════════════════
        # [V1] SQL INJECTION — Raw f-string query
        # Kali attack: sqlmap -u "http://HOST:5000/login"
        #              --data "username=admin&password=x" --dump
        # Manual:      username = alice' OR '1'='1' --
        # ════════════════════════════════════════════
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{hashed}'"
        user  = conn.execute(query).fetchone()
        conn.close()

        if user:
            token = create_token(user['id'], user['username'])
            session['token']    = token
            session['user_id']  = user['id']
            session['username'] = user['username']
            log_activity(user['id'], 'LOGIN', request.remote_addr, 'Success')
            return redirect(url_for('dashboard'))
        else:
            # [V2] No lockout — Hydra can brute-force endlessly
            log_activity(0, 'LOGIN_FAILED', request.remote_addr, f'Failed for {username}')
            return render_template_string(LOGIN_HTML, error='Invalid credentials')

    return render_template_string(LOGIN_HTML, error=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email    = request.form['email']
        hashed   = hash_password(password)
        conn     = get_db()
        try:
            conn.execute('INSERT INTO users (username,email,password) VALUES (?,?,?)',
                         (username, email, hashed))
            conn.commit()
            user = conn.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone()
            uid  = user['id']
            conn.execute('INSERT INTO wallets (user_id,balance) VALUES (?,?)', (uid, 100.0))
            conn.execute('INSERT INTO assets (user_id,name,type,value) VALUES (?,?,?,?)',
                         (uid, 'Genesis Avatar Skin', 'NFT', 50.0))
            conn.execute('INSERT INTO assets (user_id,name,type,value) VALUES (?,?,?,?)',
                         (uid, 'Virtual Land Plot #001', 'LAND', 200.0))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template_string(REGISTER_HTML, error='Username already taken')
        conn.close()
        return redirect(url_for('login'))
    return render_template_string(REGISTER_HTML, error=None)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn   = get_db()
    user   = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    wallet = conn.execute('SELECT * FROM wallets WHERE user_id=?', (session['user_id'],)).fetchone()
    assets = conn.execute('SELECT * FROM assets WHERE user_id=?', (session['user_id'],)).fetchall()
    logs   = conn.execute(
        'SELECT * FROM activity_logs WHERE user_id=? ORDER BY id DESC LIMIT 8',
        (session['user_id'],)).fetchall()
    conn.close()
    # Generate a sample tx hash to display
    tx_hash = hashlib.sha256(f"session_{session['user_id']}_{datetime.datetime.utcnow().date()}".encode()).hexdigest()
    return render_template_string(DASHBOARD_HTML,
        user=user, wallet=wallet, assets=assets, logs=logs,
        token=session.get('token',''), tx_hash=tx_hash)

@app.route('/transfer', methods=['POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    amount  = float(request.form.get('amount', 0))
    to_user = request.form.get('to_user', '')
    conn    = get_db()
    wallet  = conn.execute('SELECT * FROM wallets WHERE user_id=?', (session['user_id'],)).fetchone()
    if wallet and wallet['balance'] >= amount > 0:
        to = conn.execute('SELECT id FROM users WHERE username=?', (to_user,)).fetchone()
        if to:
            conn.execute('UPDATE wallets SET balance=balance-? WHERE user_id=?',
                         (amount, session['user_id']))
            conn.execute('UPDATE wallets SET balance=balance+? WHERE user_id=?',
                         (amount, to['id']))
            tx_data = f"{session['user_id']}{to['id']}{amount}{datetime.datetime.utcnow()}"
            tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()
            conn.execute('INSERT INTO transactions (from_user,to_user,amount,tx_hash) VALUES (?,?,?,?)',
                         (session['user_id'], to['id'], amount, tx_hash))
            conn.commit()
            log_activity(session['user_id'], 'TRANSFER', request.remote_addr,
                         f'Sent {amount} MC to {to_user}')
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    log_activity(session.get('user_id', 0), 'LOGOUT', request.remote_addr, 'User logged out')
    session.clear()
    return redirect(url_for('index'))

# [V4] JWT exposed in URL — attacker can steal from browser history / logs
@app.route('/api/user')
def api_user():
    token = request.args.get('token') or session.get('token')
    if token:
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 401
    return jsonify({'error': 'No token provided'}), 401

if __name__ == '__main__':
    # [V5] debug=True exposes interactive Werkzeug debugger
    app.run(host='0.0.0.0', port=5000, debug=True)
