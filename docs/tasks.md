# Tarefas (testes primeiro)

Ciclo de cada tarefa: **RED** (rodar os testes e ver falhar), **GREEN** (código mínimo para passar), **REFACTOR**. Um commit `test:` antes de cada `feat:`.

Comando padrão: `.\.venv\Scripts\python -m pytest -q`

## Quinta, 22/10 (hoje)

- [x] T01 Copiar o pacote de testes para o repositório, instalar `pytest` e confirmar o **vermelho** (erro de importação é o esperado). Commit: `test: add failing tests and synthetic data`.
- [x] T02 Criar `src/slothguard/__init__.py` e implementar `models.py`. Commit `feat:`.
- [x] T03 GREEN de `tests/test_loaders.py` e `tests/test_rules.py` (`rules/__init__.py` e `rules/loaders.py`). Depois `tests/test_data_synthetic.py`. Commit `feat:`.
- [x] T04 Criar um tenant **gratuito** do Auth0 (sem pagar nada) e verificar se a autorização assíncrona (CIBA) pode ser habilitada e usada nele. Anotar o resultado, inclusive se o painel pedir upgrade, em `docs/evidence/auth0-notes.md` (sem segredos). **Ponto de decisão: sexta, 23/10, à tarde.** Sem CIBA gratuito, seguir com login Auth0 e gateway simulado declarado.
- [x] T05 Instalar o Ollama e medir o E2B: `ollama run gemma4:e2b --verbose`. Anotar tokens/s e as condições em `docs/evidence/ollama-baseline.md`.

## Sexta, 23/10

- [x] T04b Usuário de teste no tenant do Auth0 com push cadastrado no app Guardian (feito em 23/10: o painel lista o aparelho como cadastrado por push e TOTP, e o atributo `multifactor` mostra `guardian`). Anotado em `docs/evidence/auth0-notes.md`.
- [x] T04c Teste manual de CIBA com `scripts/ciba_smoke_test.py` (feito em 23/10): aprovação (11,8 s) e recusa (5,9 s) funcionaram no tenant de avaliação, com o canal Guardian Push. Os tempos incluem a resposta humana e o intervalo de 5 s da consulta, então não são latência do Auth0. Disponibilidade depois da avaliação: não verificada.
- [ ] T06 Explicações, **testes primeiro**: (RED) `tests/test_explain.py` atualizado, com os testes novos do limite de frases; (GREEN) `src/slothguard/llm/__init__.py` com `explain_finding`, cache, texto de reserva e limite de `max_sentences=4` aplicado pelo código. Dois commits: `test:` e depois `feat:`.
- [ ] T07 Implementar `OllamaClient` enviando `think: false` (medido em 23/10: cerca de 81% menos tokens e cerca de 4,3x mais rápido) e rodar `RUN_OLLAMA_TESTS=1` em `tests/integration`. Conferir o formato da API local do Ollama na documentação oficial antes de escrever.
- [ ] T08 GREEN de `tests/test_report.py` (`report/__init__.py`).
- [ ] T09 Script `scripts/run_review.py`: carrega os dados, detecta, explica em lote com cache, grava `docs/evidence/report-sample.md`. Fechar o navegador e o ambiente do Kaggle durante a geração.
- [ ] T10 Interface mínima (somente leitura) mostrando o relatório.

## Sábado, 24/10

- [ ] T11 GREEN de `tests/test_approvals.py` (`auth/approvals.py`).
- [ ] T12 `Auth0CibaGateway`, **testes primeiro** (`tests/test_auth0_gateway.py`, com HTTP falsificado). O CIBA com push foi verificado no tenant de avaliação (T04c), então o gateway real é o caminho. Requisitos conferidos na documentação do Auth0 e no teste manual: pedido em `/bc-authorize` com `login_hint` no formato `iss_sub`, `scope=openid`, `binding_message` obrigatória (até 64 caracteres, só alfanuméricos e `+-_.,:#`) e `requested_expiry` de até 300 s para usar o push; consulta a `/oauth/token` com o grant `urn:openid:params:grant-type:ciba` a cada cerca de 5 s, respeitando `slow_down`; no máximo 5 pedidos por minuto por usuário. Mapeamento: `authorization_pending` vira `PENDING`; token recebido vira `APPROVED`; `access_denied` dentro do prazo vira `DENIED`; prazo local vencido sem resposta vira `EXPIRED` (a documentação usa `access_denied` para recusa e expiração, então o relógio local decide). Credenciais só do `.env`, nunca impressas. Se o CIBA deixar de estar disponível, usar gateway simulado e declarar isso no README e no post.
- [ ] T13 Login via Auth0 na interface e botão "propor revogação" ligado ao `RemediationExecutor`; trilha de auditoria visível.
- [ ] T14 Teste ponta a ponta manual do fluxo de aprovação. Gravar o vídeo de demonstração (com os explicativos já em cache, e dizer isso no post). A avaliação do Auth0 tinha 21 dias restantes em 23/10, o que cobre o desafio; o post diz que o CIBA foi usado durante a avaliação.
- [ ] T15 Medir o tempo economizado: revisão manual de uma amostra contra o relatório do agente. Salvar em `docs/evidence/lazy-payoff.md`.

## Domingo, 25/10

- [ ] T16 Rascunho do post em inglês em `docs/post/draft.md`, seguindo o template da Semana 3 (inclusive "Prize Categories": Auth0 e Gemma, só se realmente usados).
- [ ] T17 README final: instruções, créditos, commits após o prazo (se houver).
- [ ] T18 Varredura de segredos no histórico, tornar o repositório **público** e conferir que o link abre sem login.
- [ ] T19 Publicar no DEV com as tags `devchallenge` e `hf26challenge`, **antes das 23h59 PDT do dia 25** (03h59 de 26/10 em Brasília). Meta: publicar na noite de 25/10, no horário de Brasília.
