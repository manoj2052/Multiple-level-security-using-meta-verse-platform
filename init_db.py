"""
init_db.py — Run this ONCE before starting the app
Creates the SQLite database and seeds sample users.

Sample credentials for demo:
  alice / password123   (main victim account — rich wallet)
  bob   / bob2024       (secondary user)
  admin / admin123      (admin account — valuable target)
"""
import sqlite3, hashlib

def hash_password(pw):
    # SHA-256 without salt (intentionally weak for Phase 1 demo)
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('metaverse.db')
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
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (from_user) REFERENCES users(id),
        FOREIGN KEY (to_user)   REFERENCES users(id)
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

    # ── Seed users ──
    users = [
        ('alice', 'alice@metaverse.io', hash_password('password123'), 850.0),
        ('bob',   'bob@metaverse.io',   hash_password('bob2024'),     320.0),
        ('admin', 'admin@metaverse.io', hash_password('admin123'),   2500.0),
    ]

    assets_data = {
        'alice': [
            ('Legendary Dragon Skin',      'NFT',  350.0),
            ('Virtual Penthouse #A12',     'LAND', 800.0),
            ('Rare Weapon Collection',     'NFT',  220.0),
        ],
        'bob': [
            ('Blue Avatar Hoodie',         'NFT',   75.0),
            ('Forest Land Plot #B04',      'LAND', 300.0),
        ],
        'admin': [
            ('Admin Genesis Badge',        'NFT', 1200.0),
            ('Central Plaza Land #000',    'LAND',2000.0),
            ('Founders Edition Artifact',  'NFT',  900.0),
        ],
    }

    for username, email, pw_hash, balance in users:
        try:
            c.execute('INSERT INTO users (username,email,password) VALUES (?,?,?)',
                      (username, email, pw_hash))
            conn.commit()
            uid = c.lastrowid
            c.execute('INSERT OR IGNORE INTO wallets (user_id,balance) VALUES (?,?)', (uid, balance))
            for name, atype, val in assets_data.get(username, []):
                c.execute('INSERT INTO assets (user_id,name,type,value) VALUES (?,?,?,?)',
                          (uid, name, atype, val))
            conn.commit()
            print(f'[+] Created user: {username} / password hash stored | Wallet: {balance} MC')
        except sqlite3.IntegrityError:
            print(f'[!] User {username} already exists — skipping')

    conn.close()
    print('\n[✓] Database initialized → metaverse.db')
    print('─' * 50)
    print('Login credentials:')
    print('  alice  / password123')
    print('  bob    / bob2024')
    print('  admin  / admin123')
    print('─' * 50)

if __name__ == '__main__':
    init_db()
