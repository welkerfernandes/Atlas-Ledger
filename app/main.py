import os
from pathlib import Path
from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, model_validator
from .platform import tenant
from .service import Ledger

class Account(BaseModel):
    id: str = Field(min_length=1, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')
    opening_balance_cents: int = Field(ge=0, le=10**12, strict=True)

class Transfer(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    destination: str = Field(min_length=1, max_length=80)
    amount_cents: int = Field(gt=0, le=10**12, strict=True)
    idempotency_key: str = Field(min_length=1, max_length=128)

    @model_validator(mode='after')
    def different_accounts(self):
        if self.source == self.destination:
            raise ValueError('Source and destination must differ')
        return self

def create_app(path=None):
    app = FastAPI(title='Atlas Ledger', version='1.0.0')
    ledger = Ledger(path or os.getenv('DATABASE_PATH', 'ledger.db'))

    @app.get('/', response_class=HTMLResponse)
    def console(): return Path(__file__).with_name('console.html').read_text(encoding='utf-8')

    @app.get('/health')
    def health(): return {'status': 'ok'}

    @app.post('/accounts', status_code=201)
    def account(command: Account, identity: str = Depends(tenant)):
        return ledger.account(identity, command.id, command.opening_balance_cents)

    @app.post('/transfers')
    def transfer(command: Transfer, identity: str = Depends(tenant)):
        return ledger.transfer(identity, command)

    @app.get('/ledger')
    def snapshot(identity: str = Depends(tenant)): return ledger.snapshot(identity)

    return app

app = create_app()
