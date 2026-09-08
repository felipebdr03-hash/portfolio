# Otimização de Portfólio B3, v3

Versão revisada do projeto walk-forward.

## Principais correções
- Warm-up de `LOOKBACK_MONTHS` antes do início do backtest.
- Primeira montagem da carteira tratada como 100% de turnover.
- Risk Parity verifica convergência.
- Risk Parity não renormaliza pesos após aplicar o limite máximo.
- Markowitz usa taxa anualizada baseada no CDI observado até cada rebalanceamento.
- Sharpe e Sortino usam CDI diário.
- Benchmarks e estratégias são alinhados ao período comum.
- `END_DATE` é respeitado no último período.
- Teste de múltiplos períodos também recebe warm-up.

## Execução

```bash
pip install yfinance pandas numpy scipy matplotlib requests PyPortfolioOpt
python walk_forward_backtest.py
python sensitivity_analysis.py
python multi_period_test.py
```

## Limitações ainda existentes

1. O filtro fundamentalista usa snapshot atual do yfinance, portanto ainda existe look-ahead fundamentalista.
2. O universo atual ainda sofre survivorship bias.
3. Sensitivity analysis é exploratória e não deve ser usada para escolher parâmetros e depois chamar o mesmo período de teste independente.
4. Ainda falta separar formalmente desenvolvimento, validação e teste final intocado.

## Próxima grande etapa

Construir fundamentos point-in-time e universo histórico sem survivorship bias.

Depois disso, avaliar HRP, FIIs e renda fixa.
