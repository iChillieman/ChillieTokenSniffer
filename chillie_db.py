import sqlite3

RUG_PULL = "rugpull"
GARBAGE = "garbage"
UNSELLABLE = 'unsellable'
ZERO_BALANCE = "zero"
HONEYPOT = "honeypot"
db_name = 'SniffSniff.db'

def create_tables():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("""CREATE TABLE event (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NULL
            )""")

    c.execute("""CREATE TABLE sale (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hex TEXT NOT NULL,
                sale REAL NOT NULL,
                gas REAL NOT NULL,
                estimated_tax REAL NOT NULL
            )""")

    c.execute("""CREATE TABLE sell_estimate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hex TEXT NOT NULL,
                sale REAL NOT NULL,
                gain REAL NOT NULL,
                time REAL NOT NULL
            )""")

    c.execute("""CREATE TABLE buy_estimate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hex TEXT NOT NULL,
                amount REAL NOT NULL,
                gas REAL NOT NULL
            )""")

    c.execute("""CREATE TABLE buy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hex TEXT NOT NULL,
                investment REAL NOT NULL,
                amount REAL NULL
            )""")

    c.execute("""CREATE TABLE abi (
                hex TEXT PRIMARY KEY,
                abi TEXT NOT NULL
            )""")

    c.execute("""CREATE TABLE bad_token (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hex TEXT NOT NULL,
                reason TEXT NOT NULL
            )""")

    c.execute("""CREATE TABLE ready_to_watch (
                hex TEXT PRIMARY KEY
            )""")

    c.execute("""CREATE TABLE watching (
                hex TEXT PRIMARY KEY,
                start_time REAL NOT NULL
            )""")

    c.execute("""CREATE TABLE estimate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hex TEXT NOT NULL,
                sale REAL NOT NULL,
                gain REAL NOT NULL
            )""")

    c.execute("""CREATE TABLE checkpoint (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hex TEXT NOT NULL,
                checkpoint INTEGER NOT NULL,
                gain REAL NOT NULL
            )""")

    c.execute("""CREATE TABLE estimate_event (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )""")

    #This hishest honor for a token:
    c.execute("""CREATE TABLE reserves (
                hex TEXT PRIMARY KEY
            )""")

    c.execute("""CREATE TABLE allowance_request (
                hex TEXT PRIMARY KEY
            )""")

    conn.commit()
    conn.close()

def temp():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("""CREATE TABLE checkpoint (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hex TEXT NOT NULL,
                checkpoint INTEGER NOT NULL
            )""")

    conn.commit()
    conn.close()

    
def refresh_estimate_tables():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("DROP TABLE estimate")
    c.execute("DROP TABLE estimate_event")

    c.execute("""CREATE TABLE estimate_event (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )""")

    c.execute("""CREATE TABLE estimate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hex TEXT NOT NULL,
                sale REAL NOT NULL,
                gain REAL NOT NULL
            )""")

    conn.commit()
    conn.close()
    
def db_insert_ready_to_watch(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO ready_to_watch VALUES (:hex)", 
            {'hex': hex}
        )

    conn.commit()
    conn.close()

def insert_watching(hex, start_time):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO watching VALUES (:hex, :start_time)", 
            {'hex': hex, 'start_time': start_time}
        )

    conn.commit()
    conn.close()


def insert_reserves(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO reserves VALUES (:hex)", 
            {'hex': hex}
        )

    conn.commit()
    conn.close()

def insert_abi(hex, abi):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO abi VALUES (:hex, :abi)", 
            {'hex': hex, 'abi': abi}
        )

    conn.commit()
    conn.close()

def insert_position(hex, amount):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO position VALUES (null, :hex, :amount)", 
            {'hex': hex, 'amount': amount}
        )

    conn.commit()
    conn.close()

def insert_checkpoint(hex, checkpoint, gain):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO checkpoint VALUES (null, :hex, :checkpoint, :gain)", 
            {'hex': hex, 'checkpoint': checkpoint, 'gain': gain}
        )

    conn.commit()
    conn.close()

def insert_rug_pull(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO bad_token VALUES (null, :hex, :reason)", 
            {'hex': hex, 'reason': RUG_PULL}
        )

    conn.commit()
    conn.close()

def insert_zero_balance(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO bad_token VALUES (null, :hex, :reason)", 
            {'hex': hex, 'reason': ZERO_BALANCE}
        )

    conn.commit()
    conn.close()

def insert_honeypot(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO bad_token VALUES (null, :hex, :reason)", 
            {'hex': hex, 'reason': HONEYPOT}
        )

    conn.commit()
    conn.close()

def insert_unsellable(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO bad_token VALUES (null, :hex, :reason)", 
            {'hex': hex, 'reason': UNSELLABLE}
        )

    conn.commit()
    conn.close()

def insert_garbage(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO bad_token VALUES (null, :hex, :reason)", 
            {'hex': hex, 'reason': GARBAGE}
        )

    conn.commit()
    conn.close()

def db_insert_event(event_string):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO event VALUES (null, :name)", 
            {'name': event_string}
        )

    conn.commit()
    conn.close()

def insert_estimate_event(event_string):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("INSERT INTO estimate_event VALUES (null, :name)", 
            {'name': event_string}
        )

    conn.commit()
    conn.close()

def db_insert_buy_estimate(hex, amount, estimated_gas):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute(
        "INSERT INTO buy_estimate VALUES (null, :hex, :amount, :gas)" , 
        {'hex': hex, 'amount': amount, 'gas': estimated_gas}
    )

    conn.commit()
    conn.close()

def insert_sell_estimate(hex, sale, gain, time):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute(
        "INSERT INTO sell_estimate VALUES (null, :hex, :sale, :gain, :time)" , 
        {'hex': hex, 'sale': sale, 'gain': gain, 'time': time}
    )

    conn.commit()
    conn.close()

def insert_sale(hex, sale, gas, estimated_tax):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute(
        "INSERT INTO sale VALUES (null, :hex, :sale, :gas, :estimated_tax)" , 
        {'hex': hex, 'sale': sale, 'gas': gas, 'estimated_tax': estimated_tax}
    )

    conn.commit()
    conn.close()

def insert_allowance_request(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute(
        "INSERT INTO allowance_request VALUES (:hex)" , 
        {'hex': hex}
    )

    conn.commit()
    conn.close()

def db_insert_buy(hex, investment):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute(
        "INSERT INTO buy VALUES (null, :hex, :investment, 0)" , 
        {'hex': hex, 'investment': investment}
    )

    conn.commit()
    conn.close()

def update_starting_balance(hex, amount):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute(
        "UPDATE buy SET amount=:amount WHERE hex=:hex " , 
        {'hex': hex, 'amount': amount}
    )

    conn.commit()
    conn.close()

def insert_estimate(hex, estimated_sale_price, gain):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute(
        "INSERT INTO estimate VALUES (null, :hex, :sale, :gain)" , 
        {'hex': hex, 'sale': estimated_sale_price, 'gain': gain}
    )

    conn.commit()
    conn.close()


def fetch_sold_count(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM sale WHERE hex=:hex", {'hex': hex}) 
    sold = c.fetchone()
    conn.close()

    return sold[0]

def fetch_starting_balance(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT amount FROM buy WHERE hex=:hex", {'hex': hex}) 
    balance = c.fetchone()
    conn.close()
    if balance == None:
        return 0
    else:
        return balance[0]

def fetch_abi(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT abi FROM abi WHERE hex=:hex", {'hex': hex}) 
    abi = c.fetchone()
    conn.close()

    return abi

def db_fetch_all_buy_estimates():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT * FROM buy_estimate")
    
    all_buy_estimates = c.fetchall()

    conn.close()
    return all_buy_estimates

def db_fetch_all_buys():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT * FROM buy")
    
    all_buys = c.fetchall()

    conn.close()
    return all_buys

def db_fetch_all_garbage():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT hex, COUNT(*) FROM bad_token WHERE reason=:reason GROUP BY hex", {'reason': GARBAGE})
    
    all_garbage = c.fetchall()

    conn.close()
    return all_garbage

def db_fetch_all_unsellable():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT hex, COUNT(*) FROM bad_token WHERE reason=:reason GROUP BY hex", {'reason': UNSELLABLE})
    
    all_garbage = c.fetchall()

    conn.close()
    return all_garbage

def fetch_all_zero_balance():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT hex FROM bad_token WHERE reason=:reason", {'reason': ZERO_BALANCE})
    
    all_zeros = c.fetchall()

    conn.close()
    return all_zeros

def db_fetch_all_rug_pulls():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT * FROM bad_token WHERE reason=:reason", {'reason': RUG_PULL})
    
    all_pulls = c.fetchall()

    conn.close()
    return all_pulls

def fetch_all_watching():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT * FROM watching")
    
    all_tokens_being_watched = c.fetchall()

    conn.close()
    return all_tokens_being_watched
    
def fetch_all_ready_to_watch():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT * FROM ready_to_watch")
    
    all_tokens_ready = c.fetchall()

    conn.close()
    return all_tokens_ready

def is_allowance_already_requested(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT * FROM allowance_request WHERE hex=:hex", {'hex': hex})
    
    allowance = c.fetchall()

    conn.close()
    if len(allowance) == 0:
        return False
    else:
        return True

def remove_ready_to_watch(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("DELETE FROM ready_to_watch where hex=:hex", 
            {'hex': hex}
        )

    conn.commit()
    conn.close()

def remove_watching(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("DELETE FROM watching where hex=:hex", 
            {'hex': hex}
        )

    conn.commit()
    conn.close()

def remove_buy_estimate(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("DELETE FROM buy_estimate where hex=:hex", 
            {'hex': hex}
        )

    conn.commit()
    conn.close()

def remove_buy(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("DELETE FROM buy where hex=:hex", 
            {'hex': hex}
        )

    conn.commit()
    conn.close()

def remove_garbage(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("DELETE FROM bad_token where hex=:hex AND reason=:reason", 
            {'hex': hex, 'reason': GARBAGE}
        )

    conn.commit()
    conn.close()

def remove_unsellable(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("DELETE FROM bad_token where hex=:hex AND reason=:reason", 
            {'hex': hex, 'reason': UNSELLABLE}
        )

    conn.commit()
    conn.close()

def remove_rug_pull(hex):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("DELETE FROM bad_token where hex=:hex AND reason=:reason", 
            {'hex': hex,  'reason': RUG_PULL}
        )

    conn.commit()
    conn.close()

    