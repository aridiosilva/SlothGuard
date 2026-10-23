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
| FR-05 | Explicar com no máximo 4 frases, **aplicado pelo código** e não só pelo prompt (medido em 23/10: 1 de 6 respostas passou do limite); usar texto padrão se o modelo falhar, devolver vazio ou passar do limite; não guardar texto padrão no cache | `tests/test_explain.py` |
| FR-06 | Relatório em Markdown com resumo por gravidade, um bloco por achado, origem do texto e aviso quando não há explicação | `tests/test_report.py` |
| FR-07 | Nenhuma revogação sem aprovação; falha fechada; só `revoke_role`; execução idempotente | `tests/test_approvals.py` |
| FR-08 | Trilha de auditoria: proposed, approved/denied/expired, executed/error | `tests/test_approvals.py` |
| FR-09 | Cliente do Ollama devolve texto de um modelo local (teste de integração, opcional) | `tests/integration/test_ollama_live.py` |

## 4. Contrato dos módulos (o que os testes importam)

| Importação | Símbolos |
|---|---|
| `slothguard.models` | `UserAccess(user_id, name, unit, roles: frozenset)`, `SoDRule(id, name, conflicting_roles: tuple de 2, severity, description)`, `Finding(rule_id, user_id, roles: tuple, severity)`; todos imutáveis |
| `slothguard.rules` | `detect_conflicts(users, rules) -> list[Finding]`, `load_users(path)`, `load_rules(path)` (lançam `ValueError` para entrada inválida e `FileNotFoundError` para arquivo ausente) |
| `slothguard.llm` | `Explanation(text, source)` com `source` em `"model"`, `"cache"`, `"fallback"`; `ExplanationCache` com `get(finding)` e `put(finding, text)`; `explain_finding(finding, rule, client, cache=None, max_sentences=4) -> Explanation`; `count_sentences(text) -> int`; `MAX_SENTENCES = 4`; `OllamaClient(host, model)` com `generate(prompt) -> str`, que envia `think: false` |
| `slothguard.auth.approvals` | `ApprovalStatus` (`PENDING`, `APPROVED`, `DENIED`, `EXPIRED`), `RemediationAction(kind, user_id, role, rule_id)`, `PendingRemediation(request_id, action)`, `AuditEntry(event, request_id, user_id, role)`, `RemediationExecutor(gateway, revoker)` com `propose(action)`, `execute(pending)` e `audit` |
| `slothguard.report` | `build_report(findings, explanations, generated_on: date) -> str`, com `explanations` indexado por `(rule_id, user_id)` |

`execute` devolve uma destas strings: `"executed"`, `"already_executed"`, `"waiting"`, `"denied"`, `"expired"`, `"error"`.

Regra do limite de frases: uma resposta do modelo com mais de `max_sentences` frases é descartada e substituída pelo texto de reserva (`source="fallback"`), que não vai para o cache. Frases são contadas pelo código (`count_sentences`), que separa em ponto, exclamação ou interrogação seguidos de espaço e de uma letra maiúscula ou número.

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

Tudo é feito em um tenant **do Auth0 sem pagar nada** (princípio 11 da constituição). O tenant está em um período de avaliação gratuito (21 dias restantes em 23/10/2026).

- Login via Universal Login (nível 1 do Auth0): ainda não testado.
- Aprovação assíncrona (CIBA) de ponta a ponta (nível 2): **verificada em 23/10/2026** com `scripts/ciba_smoke_test.py`. A aprovação no celular retornou `APPROVED` (11,8 s) e a recusa retornou `DENIED or expired` (5,9 s), pelo canal Guardian Push, com o usuário de teste cadastrado no app Auth0 Guardian. Os tempos incluem a resposta humana e o intervalo de 5 s da consulta, então não são latência do Auth0. **As fontes divergiam** sobre o plano gratuito (o anúncio oficial dizia que incluía a autorização assíncrona, e páginas da documentação diziam que exigia Enterprise ou complemento); o teste resolve a dúvida só para o período de avaliação. **Disponibilidade depois da avaliação: não verificada**, e o post deve dizer que foi usado durante a avaliação.
- Pré-requisitos confirmados no teste: CIBA habilitado na aplicação `slothguard-web` (Regular Web Application), fator Push do Guardian ligado em Security > Multi-factor Auth, e usuário de teste com e-mail verificado e cadastrado no push. O canal de e-mail (complemento pago) ficou desligado.

## 8. Extra, só se sobrar tempo

Auth0 FGA para limitar o que o RAG recupera por perfil, somente se estiver disponível no plano gratuito (não verificado).

## 9. Riscos conhecidos

- Velocidade do modelo em CPU de 15 W com memória em canal único: medir antes de prometer qualquer número.
- RAM quase toda ocupada na máquina de desenvolvimento: fechar programas antes de carregar o modelo.
- CIBA depois do período de avaliação do Auth0: não verificado (ver item 7). Se deixar de estar disponível, o fallback é o gateway simulado, declarado no post.
- Qualidade do texto do modelo: em 23/10, a palavra "critical" apareceu em 4 de 6 respostas com gravidade "high", e 1 resposta passou do limite de 4 frases. A gravidade vem sempre das regras, e o limite de frases é aplicado pelo código.

## 10. Gateway do Auth0 CIBA (tarefa T12): requisitos verificados

Conferidos na documentação do Auth0 e no teste manual de 23/10/2026:

- Pedido em `/bc-authorize` (formulário): `client_id`, `client_secret`, `login_hint` com `{"format": "iss_sub", "iss": "https://<domínio>/", "sub": "<user_id>"}`, `scope=openid`, `binding_message` e `requested_expiry`.
- `binding_message`: obrigatória, até 64 caracteres, só alfanuméricos e `+-_.,:#`.
- `requested_expiry` de até 300 s usa o canal de push; de 301 a 259200 s usa o e-mail (complemento pago, desligado).
- Resposta: `auth_req_id`, `expires_in` e `interval` (cerca de 5 s). Consulta em `/oauth/token` com o grant `urn:openid:params:grant-type:ciba`; `authorization_pending` enquanto espera; `slow_down` pede intervalo maior; `access_denied` para recusa **e** para expiração.
- No máximo 5 pedidos por minuto por usuário.
- Mapeamento para `ApprovalStatus`: `authorization_pending` = `PENDING`; token recebido = `APPROVED`; `access_denied` antes do prazo local = `DENIED`; prazo local vencido sem resposta = `EXPIRED`.
- Credenciais só do `.env`; nunca impressas nem registradas na trilha de auditoria.
