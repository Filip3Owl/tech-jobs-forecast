# Dados externos (snapshot manual)

## `bls_projections_2025_2035.csv`

- **Fonte:** U.S. Bureau of Labor Statistics — Employment Projections, tabela
  *Occupational projections and worker characteristics* (projeções 2025–2035).
  https://www.bls.gov/emp/tables/occupational-projections-and-characteristics.htm
- **Coletado em:** 2026-10-25 (o site do BLS bloqueia download automatizado, por isso o snapshot).
- **Unidades:** emprego em milhares; `change_pct` = variação % 2025–35;
  `annual_openings` = média anual de vagas (milhares); `median_wage_2025` em US$/ano.
- **Escopo:** total de ocupações + grupo SOC 15 (computação e matemática).
- **Validação:** `tests/test_data_integrity.py` confere que os subgrupos somam os totais
  da hierarquia SOC e que `change_pct` é coerente com os níveis de emprego.
