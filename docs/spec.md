# Especificação: SlothGuard

Auditor preguiçoso de acessos: lê um export de usuários e papéis, encontra conflitos de segregação de funções (SoD), explica cada achado com um modelo local e monta o relatório. Para remediar, propõe a revogação de um papel e espera a aprovação de um humano pelo Auth0.

## 1. Problema e usuário

Quem faz revisão periódica de acessos (GRC, auditoria interna) gasta horas cruzando planilhas de papéis. O SlothGuard faz o cruzamento e a redação, e deixa a decisão com o humano.

## 2. Fluxo

1. Carregar usuários e regras (JSON).
2. Detectar conflitos com `detect_conflicts` (determinístico).
3. Explicar cada achado com o modelo local (`explain_finding`), com cache e texto padrão de reserva.
4. Montar o relatório em Markdown (`build_report`).
5. Propor a revogação de um papel (`RemediationExecutor.propose`).
6. Aguardar a aprovação humana (autorização assíncrona do Auth0).
7. Executar só se aprovado e registrar a auditoria (`RemediationExecutor.execute`).

## 3. Requisitos funcionais e testes

| ID | Requisito | Teste |
|---|---|---|
| FR-01 | Detectar usuário que tem os dois papéis de uma regra; comparação sem diferenciar maiúsculas/minúsculas e ignorando espaços nas pontas | `tests/test_rules.py` |
| FR-02 | Um achado por par usuário-regra; resultado ordenado por gravidade (high, medium, low), depois usuário, depois regra; independente da ordem de entrada | `tests/test_rules.py` |
| FR-03 | Validar entradas: regra com exatamente 2 papéis distintos, gravidade válida, ids únicos, campos obrigatórios | `tests/test_loaders.py` |
| FR-04 | Dados do repositório são sintéticos, com tamanho mínimo e com achados reais | `tests/test_data_synthetic.py` |
| FR-05 | Explicar com no máximo 4 frases; usar texto padrão se o modelo falhar ou devolver vazio; não guardar texto padrão no cache | `tests/test_explain.py` |
| FR-06 | Relatório em Markdown com resumo por gravidade, um bloco por achado, origem do texto e aviso quando não há explicação | `tests/test_report.py` |
| FR-07 | Nenhuma revogação sem aprovação; falha fechada; só `revoke_role`; execução idempotente | `tests/test_approvals.py` |
| FR-08 | Trilha de auditoria: proposed, approved/denied/expired, executed/error | `tests/test_approvals.py` |
| FR-09 | Cliente do Ollama devolve texto de um modelo local (teste de integração, opcional) | `tests/integration/test_ollama_live.py` |

## 4. Contrato dos módulos (o que os testes importam)

| Importação | Símbolos |
|---|---|
| `slothguard.models` | `UserAccess(user_id, name, unit, roles: frozenset)`, `SoDRule(id, name, conflicting_roles: tuple de 2, severity, description)`, `Finding(rule_id, user_id, roles: tuple, severity)`; todos imutáveis |
| `slothguard.rules` | `detect_conflicts(users, rules) -> list[Finding]`, `load_users(path)`, `load_rules(path)` (lançam `ValueError` para entrada inválida e `FileNotFoundError` para arquivo ausente) |
| `slothguard.llm` | `Explanation(text, source)` com `source` em `"model"`, `"cache"`, `"fallback"`; `ExplanationCache` com `get(finding)` e `put(finding, text)`; `explain_finding(finding, rule, client, cache=None) -> Explanation`; `OllamaClient(host, model)` com `generate(prompt) -> str` |
| `slothguard.auth.approvals` | `ApprovalStatus` (`PENDING`, `APPROVED`, `DENIED`, `EXPIRED`), `RemediationAction(kind, user_id, role, rule_id)`, `PendingRemediation(request_id, action)`, `AuditEntry(event, request_id, user_id, role)`, `RemediationExecutor(gateway, revoker)` com `propose(action)`, `execute(pending)` e `audit` |
| `slothguard.report` | `build_report(findings, explanations, generated_on: date) -> str`, com `explanations` indexado por `(rule_id, user_id)` |

`execute` devolve uma destas strings: `"executed"`, `"already_executed"`, `"waiting"`, `"denied"`, `"expired"`, `"error"`.

Interfaces que as peças reais devem cumprir (nos testes são falsificadas):
- **Gateway de aprovação** (`Auth0CibaGateway`, em `src/slothguard/auth/`): `request_approval(action) -> request_id` e `get_status(request_id) -> ApprovalStatus`.
- **Revogador**: `revoke(user_id, role) -> None`. No MVP atua sobre os dados sintéticos em memória, sem sistema externo.

## 5. Dados

`data/synthetic/users.json`: lista de `{user_id, name, unit, roles[], synthetic: true}`.
`data/synthetic/sod_rules.json`: lista de `{id, name, conflicting_roles[2], severity, description}`.

O conjunto fornecido tem 40 usuários e 9 regras. Em uma execução de verificação (implementação provisória, fora deste repositório), ele gerou 8 achados em 8 usuários: 5 high, 2 medium e 1 low.

## 6. Critérios de aceite do MVP

1. `python -m pytest -q` passa por inteiro (o teste de integração fica "skipped" sem `RUN_OLLAMA_TESTS=1`).
2. Com o Ollama rodando, o relatório sai com explicações de modelo local e, com o Ollama parado, sai com `Source: fallback`.
3. Login via Auth0 funcionando na interface.
4. A revogação só ocorre depois de aprovação real no Auth0, e a trilha de auditoria aparece na tela.
5. README com instruções de execução e créditos.

## 7. Verificação manual (sem teste automatizado, por depender do tenant Auth0)

- Login via Universal Login.
- Fluxo de aprovação assíncrona (CIBA) de ponta a ponta. **Verificar no primeiro dia se o plano do tenant oferece o recurso.** Se não oferecer, registrar a limitação no post e usar um gateway simulado, sem declarar uso do recurso.

## 8. Extra, só se sobrar tempo

Auth0 FGA para limitar o que o RAG recupera por perfil.

## 9. Riscos conhecidos

- Velocidade do modelo em CPU de 15 W com memória em canal único: medir antes de prometer qualquer número.
- RAM quase toda ocupada na máquina de desenvolvimento: fechar programas antes de carregar o modelo.
- CIBA no plano do Auth0: ver item 7.
