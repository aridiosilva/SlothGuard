# SlothGuard

[Read in English](README.md)

Um revisor de acessos preguiçoso. Regras simples encontram conflitos de segregação de funções (SoD),
um modelo pequeno de pesos abertos, rodando no seu próprio computador, explica cada um, e nada é
revogado a menos que um humano aprove no celular, pelo Auth0.

> **As regras detectam, o modelo explica, um humano aprova.**
> O modelo nunca decide o que é um achado nem qual a gravidade, e nunca toca em uma permissão.

Feito para o [Hacktoberfest Open-Source AI Challenge, Semana 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19), do DEV.
Projeto iniciado em 22/10/2026 (janela do desafio: 19/10/2026 a 25/10/2026).

Todos os dados são sintéticos. Uma "revogação" só altera uma cópia desses dados na memória.

## O que ele faz

1. Carrega usuários e papéis (`data/synthetic/users.json`) e regras de SoD (`data/synthetic/sod_rules.json`).
2. Encontra todo usuário que tem os dois papéis de uma regra (código determinístico; a gravidade vem da regra).
3. Pede a um modelo local (Gemma 4 E2B, pelo Ollama) uma explicação curta de cada achado. O código
   limita a resposta a quatro frases; se o modelo falhar, não responder nada ou passar do limite,
   usa-se um texto fixo e o motivo é registrado.
4. Monta um relatório em Markdown.
5. Em uma pequena interface web (login com o Auth0), uma pessoa pode propor a revogação de um papel.
   O Auth0 envia um aviso ao celular de quem aprova (Auth0 Guardian, CIBA). O papel só é revogado depois
   de "aprovar". Negado, sem resposta (120 s) ou com falha significa que nada é revogado, e cada passo
   é gravado em uma trilha de auditoria.

## Como rodar (Windows PowerShell)

Requisitos: Python 3.10 ou mais novo, o [Ollama](https://ollama.com) com o modelo baixado
(`ollama pull gemma4:e2b`) e um tenant do Auth0 (veja abaixo).

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt -r requirements.txt
Copy-Item .env.example .env        # depois preencha os valores do Auth0; nunca faça commit do .env
.\.venv\Scripts\python -m pytest -q
```

No momento em que isto foi escrito, a suíte dá `177 passed, 1 skipped` (o teste ignorado precisa do Ollama
rodando: defina `RUN_OLLAMA_TESTS=1` para executá-lo).

```powershell
.\.venv\Scripts\python scripts\run_review.py     # explica cada achado com o modelo local, salva o relatório e um registro da execução
.\.venv\Scripts\python scripts\run_app.py        # interface web em http://localhost:8000
```

Abra exatamente `http://localhost:8000` (não `127.0.0.1`): esse é o endereço registrado no Auth0.
O `run_review.py` para de imediato se o Ollama não puder ser alcançado. A página web lê as explicações
salvas pelo `run_review.py` (`data/output/explanations.json`, que não vai para o Git).

## Configuração do Auth0 (o que este projeto usou)

- Uma **Regular Web Application** com a URL de callback `http://localhost:8000/callback` e a
  URL de logout `http://localhost:8000/`.
- O tipo de concessão **Client Initiated Backchannel Authentication (CIBA)** habilitado nas configurações
  avançadas da aplicação, com o canal de notificação **Guardian Push**.
- O fator **Push Notification (Auth0 Guardian)** habilitado em Security > Multi-factor Auth.
- Um usuário de teste cadastrado no Guardian (quem aprova). O id dele no Auth0 vai em `AUTH0_TEST_USER_ID`.
- O `.env` guarda `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET` e `AUTH0_TEST_USER_ID`
  (mais `OLLAMA_HOST` e `OLLAMA_MODEL`). O `.env.example` lista os nomes, sem valores.

Nota honesta: conferi tudo isso em um tenant do Auth0 durante o período de avaliação gratuita. Não
verifiquei se a aprovação assíncrona continua disponível depois da avaliação.

## Como foi construído

```
src/slothguard/
  models.py         usuários, regras e achados imutáveis
  rules/            o motor determinístico de SoD e os leitores de JSON
  llm/              explicações (cache, texto de reserva, limite de frases) e o cliente do Ollama
  report.py + review.py   o montador do relatório e o fluxo completo da revisão
  auth/             a trava de aprovação humana (approvals.py) e o gateway CIBA do Auth0 (ciba.py)
  web/              app Flask, templates e o login com o Auth0 (Authlib)
  revoker.py        a "revogação" em memória
tests/              mais de 177 testes, escritos antes do código que cobrem
scripts/            run_review.py, run_app.py, review_quality.py e duas verificações manuais do Auth0
docs/               constituição, especificação, tarefas e docs/evidence com as medições reais
```

Os testes vieram primeiro em cada parte: o histórico mostra commits `test:` antes dos `feat:` correspondentes.
A especificação e as regras do projeto estão em `docs/constitution.md` e `docs/spec.md`.

## Medições (execuções reais, com as condições)

Veja `docs/evidence/`. Em um Dell all-in-one com Intel Core i5-1334U, 16 GB de RAM em um único canal
de memória e sem GPU dedicada, o Gemma 4 E2B pelo Ollama gerou de 13 a 22 tokens por segundo.
Desligar o trecho de raciocínio do modelo reduziu os tokens gerados em cerca de 81%. Explicar os 8 achados
levou de 97 a 157 segundos em três execuções (memória livre de 6,1, 4,3 e 1,1 GB; a variação não foi
diagnosticada). A versão do Ollama era a 0.40.8 nas medições feitas no terminal e a 0.40.10 depois.

## Limites

- Só dados sintéticos; nenhum diretório real está conectado.
- Na demonstração, quem propõe e quem aprova podem ser o mesmo usuário do Auth0. Uma implantação real precisa de duas pessoas.
- A mensagem de aprovação contém o id do usuário e o nome do papel, e esse texto vai para o Auth0.
- O servidor web é o servidor de desenvolvimento do Flask, feito para uso local.

## Créditos

Feito com ajuda de IA (em dupla com o Claude). Bibliotecas: Flask, Authlib, Requests, pytest.
Modelo: Gemma 4 E2B, executado pelo Ollama. Identidade e aprovação: Auth0 (Universal Login, CIBA, Guardian).
A documentação do Auth0 e do Ollama foi usada para os formatos dos pedidos.

## Commits depois do prazo de entrega

Nenhum até agora.
