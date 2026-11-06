# Operação local

1. Instale as dependências e execute o comando do README.
2. Verifique `GET /health` e execute o fluxo de demonstração pela console.
3. Em falhas 401, confira X-API-Key. Em 422, confira o contrato em /docs.
4. Em 409, examine conflito de negócio ou chave idempotente reutilizada.

## Configuração

`DATABASE_PATH`: caminho do arquivo SQLite; diretório pai deve existir e permitir escrita.
`API_KEYS`: objeto JSON que mapeia segredos para tenants. Exemplo somente local:

```powershell
$env:API_KEYS='{"chave-alpha":"alpha","chave-beta":"beta"}'
$env:DATABASE_PATH='./local.db'
```

## Recuperação

Pare o processo antes de copiar o arquivo SQLite para backup. Restaure para um novo caminho,
execute a suíte e valide o fluxo de negócio antes de retomar. Não copie o arquivo durante escrita.
Não há automação de backup ou garantia de RPO/RTO neste laboratório.

## Observabilidade e capacidade

Uvicorn fornece logs de acesso. Ainda não há métricas Prometheus ou tracing distribuído.
Health indica que o processo responde; não testa readiness do banco. Operações custosas são síncronas
e rodam no threadpool do FastAPI. Faça medição de carga antes de definir capacidade.
