# AgentRouter Daily

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · **Português (BR)**

O crédito diário do AgentRouter é concedido no login. Este runner entra com
usuário e senha e avalia `data.checked_in` de forma estrita.

## Contrato

```text
POST /api/user/login
body: {"username":"...","password":"..."}
```

A sessão chega em `Set-Cookie: session=...`; o fonte revisado não usa um campo
JSON `token` no corpo do login.

| `data.checked_in` | Significado | Resultado |
| :--- | :--- | :--- |
| `true` | Este login adicionou a cota diária. | `CLAIMED` |
| `false` | Login aceito, mas sem nova cota. | `NO_NEW_GRANT` |
| ausente ou não boolean | Estado não comprovado. | `CHECKIN_UNCONFIRMED` |

Não existe `/checkin` independente; o script não chama
`/api/user/checkin`.

## Credenciais

Várias contas usam `AGENTROUTER_ACCOUNTS`:

```text
label|username|password
```

A senha pode conter `|`. Uma conta pode usar `AGENTROUTER_USERNAME` e
`AGENTROUTER_PASSWORD`.

A URL padrão é `https://agentrouter.org`. Para o site doméstico, defina
`AGENTROUTER_BASE_URL=https://ps.air-outer.com`.

## Execução

```powershell
python -m pip install -r requirements.txt
$env:AGENTROUTER_USERNAME = "user@example.com"
$env:AGENTROUTER_PASSWORD = "password"
python agentrouter_daily.py
```

Somente a segunda conta:

```powershell
python agentrouter_daily.py --only 2
```

Não há modo apenas de consulta, pois o login pode conceder a cota diária.

## Estado Antes E Depois

Usuário e senha não permitem uma leitura de estado antes do login sem efeitos
colaterais. A saída explicita essa limitação:

- `checked_in=true`: antes é false pela semântica de nova concessão e depois é
  true.
- `checked_in=false`: antes é null e depois é false.
- Marcador ausente: os dois estados ficam não confirmados e o resultado falha.

Se o login devolver sessão e ID, o script lê `GET /api/user/self` para obter
quota. WAF ou captcha são registrados em `readback_error` e não viram uma
mudança de saldo inventada.

## Resultados

| Resultado | Significado |
| :--- | :--- |
| `CLAIMED` | `checked_in=true` confirmou nova cota. |
| `NO_NEW_GRANT` | Login aceito e `checked_in=false` explícito. |
| `CHECKIN_UNCONFIRMED` | Marcador ausente ou inválido. |
| `STATE_CONFLICT` | Login e user/self discordam sobre `checked_in`. |
| `AUTH_REJECTED` | Credenciais ou sessão rejeitadas. |
| `BLOCKED` | Página HTML de verificação em vez de JSON. |
| `CONFIG_ERROR` | Variáveis ou URL inválidas. |

## Actions

O workflow testa no push e executa o login no agendamento ou disparo manual,
enviando um relatório JSON como artifact. Configure as credenciais de várias
contas ou de uma conta nos Secrets.

## Testes

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check agentrouter_daily.py tests
```

Todos os testes usam respostas e sessões simuladas.

## Privacidade

Não faça commit de senhas, sessões, relatórios, capturas de tela ou dados da
conta. Apenas o rótulo mascarado é impresso.

## Licença

MIT. Consulte `LICENSE`, `NOTICE.md` e `THIRD_PARTY_NOTICES.md`.
