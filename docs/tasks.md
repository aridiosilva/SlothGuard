# Tarefas (testes primeiro)

Ciclo de cada tarefa: **RED** (rodar os testes e ver falhar), **GREEN** (código mínimo para passar), **REFACTOR**. Um commit `test:` antes de cada `feat:`.

Comando padrão: `.\.venv\Scripts\python -m pytest -q`

## Quinta, 22/10 (hoje)

- [ ] T01 Copiar o pacote de testes para o repositório, instalar `pytest` e confirmar o **vermelho** (erro de importação é o esperado). Commit: `test: add failing tests and synthetic data`.
- [ ] T02 Criar `src/slothguard/__init__.py` e implementar `models.py`. Commit `feat:`.
- [ ] T03 GREEN de `tests/test_loaders.py` e `tests/test_rules.py` (`rules/__init__.py` e `rules/loaders.py`). Depois `tests/test_data_synthetic.py`. Commit `feat:`.
- [ ] T04 Criar o tenant do Auth0 e **verificar se a autorização assíncrona (CIBA) está disponível no plano**. Anotar o resultado em `docs/evidence/auth0-notes.md` (sem segredos).
- [ ] T05 Instalar o Ollama e medir o E2B: `ollama run gemma4:e2b --verbose`. Anotar tokens/s e as condições em `docs/evidence/ollama-baseline.md`.

## Sexta, 23/10

- [ ] T06 GREEN de `tests/test_explain.py` (`llm/__init__.py`, com `explain_finding`, cache e texto padrão).
- [ ] T07 Implementar `OllamaClient` e rodar `RUN_OLLAMA_TESTS=1` em `tests/integration`. Conferir o formato da API local do Ollama na documentação oficial antes de escrever.
- [ ] T08 GREEN de `tests/test_report.py` (`report/__init__.py`).
- [ ] T09 Script `scripts/run_review.py`: carrega os dados, detecta, explica em lote com cache, grava `docs/evidence/report-sample.md`. Fechar o navegador e o ambiente do Kaggle durante a geração.
- [ ] T10 Interface mínima (somente leitura) mostrando o relatório.

## Sábado, 24/10

- [ ] T11 GREEN de `tests/test_approvals.py` (`auth/approvals.py`).
- [ ] T12 `Auth0CibaGateway` conforme a documentação do Auth0 (ou gateway simulado se o T04 mostrar que o recurso não está disponível, deixando isso explícito).
- [ ] T13 Login via Auth0 na interface e botão "propor revogação" ligado ao `RemediationExecutor`; trilha de auditoria visível.
- [ ] T14 Teste ponta a ponta manual do fluxo de aprovação. Gravar o vídeo de demonstração (com os explicativos já em cache, e dizer isso no post).
- [ ] T15 Medir o tempo economizado: revisão manual de uma amostra contra o relatório do agente. Salvar em `docs/evidence/lazy-payoff.md`.

## Domingo, 25/10

- [ ] T16 Rascunho do post em inglês em `docs/post/draft.md`, seguindo o template da Semana 3 (inclusive "Prize Categories": Auth0 e Gemma, só se realmente usados).
- [ ] T17 README final: instruções, créditos, commits após o prazo (se houver).
- [ ] T18 Varredura de segredos no histórico, tornar o repositório **público** e conferir que o link abre sem login.
- [ ] T19 Publicar no DEV com as tags `devchallenge` e `hf26challenge`, **antes das 23h59 PDT do dia 25** (03h59 de 26/10 em Brasília). Meta: publicar na noite de 25/10, no horário de Brasília.
