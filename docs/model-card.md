# Modelo, evidência e limitações

Mediana/MAD com escala mínima de 5% da mediana, mínimo de cinco transações anteriores e limiar de 3,5. A janela contém as últimas 100 transferências da conta dentro do tenant. Não há treinamento, inferência remota ou alegação de acurácia antifraude.

## Uso pretendido

Demonstração técnica e avaliação controlada com dados sintéticos. A execução é local e determinística.
Não existem métricas de produção ou benchmarks de desempenho declarados.

## Avaliação disponível

A suíte verifica comportamentos esperados, cenários adversos e invariantes. Isso não demonstra
generalização estatística em dados reais. Antes de adoção, defina um dataset independente,
critérios de aceitação, avaliação por segmento e revisão humana dos erros.

## Limitações do produto

Contas recebem um saldo inicial de laboratório; o projeto não implementa um plano contábil completo, múltiplas moedas, estornos, liquidação bancária ou reconciliação externa. A outbox é persistida, mas ainda não há dispatcher nem confirmação de entrega. O score MAD é um detector estatístico não supervisionado, não um modelo treinado de fraude. Ele sinaliza revisão e não bloqueia transferências.
