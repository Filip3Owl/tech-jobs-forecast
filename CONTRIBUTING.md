# Como contribuir

## Estratégia de branches (Git Flow simplificado)

| Branch | Papel |
|---|---|
| `main` | versões estáveis e publicadas; cada release recebe uma tag `vX.Y.Z` |
| `develop` | integração contínua das features concluídas |
| `feature/<nome>` | uma unidade de trabalho (ex.: `feature/previsao`), criada a partir de `develop` |
| `release/<versão>` | preparação de release (revisão final, versão), criada a partir de `develop` |
| `hotfix/<nome>` | correção urgente sobre `main` |

```bash
git checkout develop
git checkout -b feature/minha-analise
# ... commits ...
git checkout develop
git merge --no-ff feature/minha-analise
```

O `--no-ff` preserva no histórico o agrupamento de cada feature.

## Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/pt-br/), em português:

- `feat(escopo): ...` nova análise, modelo ou notebook
- `fix(escopo): ...` correção de bug ou de dado
- `refactor`, `docs`, `test`, `chore`, `ci`

Escopos usados: `dados`, `features`, `mineracao`, `modelos`, `viz`, `notebooks`.

## Antes de abrir um merge

1. `make test` passa.
2. `make notebooks` executa sem erro (os notebooks são versionados **com saídas**, para leitura direta no GitHub).
3. Gráficos novos usam `techdemand.style` (fundo preto, paleta validada, rótulos diretos, fonte citada).
4. Afirmações no texto dos notebooks são sustentadas por números calculados nas células.
