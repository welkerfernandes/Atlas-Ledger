# ADR 001 — Escopo executável e consistência

Status: implementado.

## Contexto

Retries de integração não podem duplicar dinheiro, e decisões de risco precisam ser explicáveis.

## Decisão

SQLite com BEGIN IMMEDIATE serializa escritores e permite testar concorrência sem infraestrutura externa. Saldo, duas partidas e evento são persistidos na mesma transação. A chave idempotente é única por tenant; reutilização com outro payload produz 409.

## Alternativas e consequências

Um monólito modular reduz pontos de falha e mantém a demonstração reproduzível.
Microsserviços adicionariam rede, observabilidade distribuída e implantação sem necessidade comprovada.
SQLite reduz dependências, mas tem um escritor por vez. PostgreSQL é a evolução para concorrência sustentada.
A troca de banco exige revisão das transações e testes; não é apenas trocar a URL.

## Fronteiras de segurança

Credencial → identidade do tenant → caso de uso → SQL com filtro por tenant.
Não há header arbitrário de identidade. Credenciais locais existem somente para demonstração.
Documentação interativa e health são públicos; operações de negócio são autenticadas.

## Evolução

Adicionar lançamentos de abertura e estorno imutáveis; migrar para PostgreSQL com bloqueio por conta; implementar dispatcher com leasing e consumidor idempotente; adicionar conciliação e avaliação com dados rotulados.
