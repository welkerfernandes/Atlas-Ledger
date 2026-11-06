# Segurança

Esta implementação é um laboratório executável, não um serviço homologado para produção.
As chaves `local-alpha` e `local-beta` existem apenas para demonstração. Antes de exposição
externa, configure `API_KEYS` com credenciais aleatórias por tenant e termine TLS no proxy.
Não utilize dados pessoais ou financeiros reais na demonstração.

O tenant é derivado da credencial; consultas usam parâmetros SQL e escopo explícito.
Não há acesso de rede a modelos externos. A console renderiza respostas com textContent.

Limitações: não há rotação de credenciais, RBAC, rate limiting distribuído, criptografia
de disco gerenciada, backup automatizado ou integração com provedor de identidade.
Relate vulnerabilidades de forma privada ao responsável pelo repositório.
