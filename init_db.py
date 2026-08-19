"""
init_db.py — Phase 3 Secure Database Setup
Passwords stored with PBKDF2-HMAC-SHA256 + salt (100,000 iterations)
"""
import sqlite3, hashlib, os

def hash_password(password):
    salt = os.urandom(32)
    key  = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000)
    return salt.hex() + ':' + key.hex()

def init_db():
    conn = sqlite3.connect('metaverse_secure.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        balance REAL DEFAULT 0.0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        type TEXT,
        value REAL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user INTEGER,
        to_user INTEGER,
        amount REAL,
        tx_hash TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        ip_address TEXT,
        details TEXT,
        timestamp TEXT
    )''')
    conn.commit()

    users = [
        ('alice', 'alice@metaverse.io', 'password123', 850.0),
        ('bob',   'bob@metaverse.io',   'bob2024',     320.0),
        ('admin', 'admin@metaverse.io', 'admin123',   2500.0),
    ]
    assets_data = {
        'alice': [('Legendary Dragon Skin', 'NFT', 350.0), ('Virtual Penthouse #A12', 'LAND', 800.0)],
        'bob':   [('Blue Avatar Hoodie', 'NFT', 75.0),     ('Forest Land Plot #B04', 'LAND', 300.0)],
        'admin': [('Admin Genesis Badge', 'NFT', 1200.0),  ('Central Plaza Land #000', 'LAND', 2000.0)],
    }

    for username, email, pw, balance in users:
        try:
            c.execute('INSERT INTO users (username,email,password) VALUES (?,?,?)',
                      (username, email, hash_password(pw)))
            conn.commit()
            uid = c.lastrowid
            c.execute('INSERT OR IGNORE INTO wallets (user_id,balance) VALUES (?,?)', (uid, balance))
            for name, atype, val in assets_data.get(username, []):
                c.execute('INSERT INTO assets (user_id,name,type,value) VALUES (?,?,?,?)',
                          (uid, name, atype, val))
            conn.commit()
            print(f'[+] Secure user created: {username} | PBKDF2-SHA256+salt | Wallet: {balance} MC')
        except sqlite3.IntegrityError:
            print(f'[!] {username} already exists')

    conn.close()
    print('\n[✓] Secure database ready → metaverse_secure.db')
    print('[✓] All passwords hashed with PBKDF2-HMAC-SHA256 + 32-byte random salt')
    print('─' * 50)
    print('Login: alice/password123  bob/bob2024  admin/admin123')

if __name__ == '__main__':
    init_db()
