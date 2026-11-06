import json
import uuid
from fastapi import HTTPException
from .platform import database, fingerprint
from .domain import anomaly

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts(tenant TEXT, id TEXT, balance INTEGER NOT NULL CHECK(balance>=0), PRIMARY KEY(tenant,id));
CREATE TABLE IF NOT EXISTS transfers(tenant TEXT, id TEXT, idem TEXT, fingerprint TEXT, source TEXT, destination TEXT, amount INTEGER CHECK(amount>0), risk TEXT, PRIMARY KEY(tenant,id), UNIQUE(tenant,idem));
CREATE TABLE IF NOT EXISTS entries(tenant TEXT, transfer_id TEXT, account TEXT, delta INTEGER NOT NULL, FOREIGN KEY(tenant,transfer_id) REFERENCES transfers(tenant,id), FOREIGN KEY(tenant,account) REFERENCES accounts(tenant,id));
CREATE TABLE IF NOT EXISTS outbox(tenant TEXT, id TEXT PRIMARY KEY, payload TEXT NOT NULL);
"""


class Ledger:
    def __init__(self, path):
        self.path = path
        with database(path) as db:
            db.executescript(SCHEMA)

    def account(self, tenant, account, balance):
        with database(self.path) as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM accounts WHERE tenant=? AND id=?', (tenant, account)).fetchone():
                raise HTTPException(409, 'Account already exists')
            db.execute('INSERT INTO accounts VALUES(?,?,?)', (tenant, account, balance))
        return {'id': account, 'opening_balance_cents': balance}

    def transfer(self, tenant, command):
        data = command.model_dump()
        digest = fingerprint({k: v for k, v in data.items() if k != 'idempotency_key'})
        with database(self.path) as db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT * FROM transfers WHERE tenant=? AND idem=?', (tenant, command.idempotency_key)).fetchone()
            if previous:
                if previous['fingerprint'] != digest:
                    raise HTTPException(409, 'Idempotency key reused with different payload')
                return {'id': previous['id'], 'risk': json.loads(previous['risk']), 'replayed': True}
            accounts = {r['id']: r['balance'] for r in db.execute('SELECT * FROM accounts WHERE tenant=? AND id IN (?,?)', (tenant, command.source, command.destination))}
            if len(accounts) != 2:
                raise HTTPException(404, 'Account not found')
            if accounts[command.source] < command.amount_cents:
                raise HTTPException(409, 'Insufficient funds')
            history = [r[0] for r in db.execute('SELECT amount FROM transfers WHERE tenant=? AND source=? ORDER BY rowid DESC LIMIT 100', (tenant, command.source))]
            risk = anomaly(command.amount_cents, history)
            ident = str(uuid.uuid4())
            db.execute('INSERT INTO transfers VALUES(?,?,?,?,?,?,?,?)', (tenant, ident, command.idempotency_key, digest, command.source, command.destination, command.amount_cents, json.dumps(risk)))
            for account, delta in [(command.source, -command.amount_cents), (command.destination, command.amount_cents)]:
                db.execute('UPDATE accounts SET balance=balance+? WHERE tenant=? AND id=?', (delta, tenant, account))
                db.execute('INSERT INTO entries VALUES(?,?,?,?)', (tenant, ident, account, delta))
            db.execute('INSERT INTO outbox VALUES(?,?,?)', (tenant, ident, json.dumps({'type': 'transfer.posted', 'transfer_id': ident})))
            return {'id': ident, 'risk': risk, 'replayed': False}

    def snapshot(self, tenant):
        with database(self.path) as db:
            accounts = [dict(r) for r in db.execute('SELECT id,balance FROM accounts WHERE tenant=? ORDER BY id', (tenant,))]
            unbalanced = db.execute('SELECT transfer_id FROM entries WHERE tenant=? GROUP BY transfer_id HAVING SUM(delta)!=0', (tenant,)).fetchall()
            events = [json.loads(r[0]) for r in db.execute('SELECT payload FROM outbox WHERE tenant=?', (tenant,))]
            return {'accounts': accounts, 'balanced': not unbalanced, 'outbox': events}
