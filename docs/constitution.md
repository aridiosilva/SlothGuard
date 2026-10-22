# Constituição do projeto SlothGuard

Regras que não mudam durante o desafio. Se um item entrar em conflito com a pressa, o item vence.

**Desafio:** DEV Hacktoberfest Open-Source AI Challenge, Semana 3 ("Slow and Steady").
**Janela:** 19/10/2026 a 25/10/2026 (entrega até 25/10/2026, 23h59 PDT, ou seja, 03h59 de 26/10 no horário de Brasília).
**Categorias-alvo:** prêmio geral, Best Use of Auth0 for AI Agents e Best Use of Gemma.

## Princípios

1. **Só dados sintéticos.** Nenhum dado real de empresa, pessoa ou sistema entra no repositório. Todo registro de `data/synthetic/users.json` traz `"synthetic": true`, e um teste verifica isso.
2. **As regras detectam; o modelo só explica.** Conflitos de segregação de funções (SoD) são encontrados por código determinístico. O modelo nunca cria, remove nem muda a gravidade de um achado. Se o modelo falhar, o relatório sai do mesmo jeito, com um texto padrão marcado como `fallback`.
3. **Nenhuma ação de risco sem aprovação humana explícita.** Revogar um papel só acontece depois de aprovação registrada. Na dúvida (erro, expiração, resposta desconhecida), o sistema **não executa** (falha fechada). A única ação suportada é `revoke_role`.
4. **Tudo que muda algo deixa rastro.** Cada proposta, decisão e execução gera uma entrada de auditoria.
5. **Segredos fora do repositório.** Credenciais do Auth0 ficam em `.env` (ignorado pelo Git). Só `.env.example`, sem valores, é versionado. Se um segredo for commitado por engano, ele é regenerado, porque o repositório será público na entrega.
6. **Testes primeiro.** Nenhum código de produção sem um teste falhando antes (vermelho, verde, refatorar). O histórico deve mostrar o commit `test:` antes do `feat:` correspondente.
7. **Números honestos.** Tudo que o post afirmar sobre velocidade ou tempo economizado vem de medição real, salva em `docs/evidence/` com as condições do teste (modelo, programas abertos, RAM livre, modo de energia). Sem número medido, o post diz "não medido".
8. **IA aberta no centro.** O modelo é open-weight, roda localmente via Ollama e é intercambiável. O post explica por que isso importa (dados de acesso não saem da máquina).
9. **Projeto novo, crédito a terceiros.** Tudo nasce dentro da janela. Código de exemplo do Auth0 ou de outros é creditado no README e no post. Commits feitos depois do prazo são listados no README.
10. **Post em inglês.** Posts em outro idioma não concorrem a prêmio.

## Definição de pronto (por tarefa)

- Os testes da tarefa passam (`python -m pytest -q`).
- Nenhum segredo ou dado real no diff.
- Commit com mensagem convencional (`test:`, `feat:`, `docs:`, `refactor:`).

## Fora de escopo

Token Vault e integrações externas (Slack, Google), fine-tuning, dados reais, múltiplos idiomas na interface, e qualquer ação além de `revoke_role`.
