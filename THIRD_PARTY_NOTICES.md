# Third-Party Notices

This repository contains an independently written Python implementation of
the AgentRouter daily login-credit flow. Credentials are supplied at runtime
and are not included in the repository.

## Protocol Evidence

### agentrouter-magpie-plugin

- Source: `ZhaoJun233/agentrouter-magpie-plugin`
- Fixed commit reviewed: `6713ffa4f2e517a1307315c9bb05c14feabe2b06`
- License: MIT
- Copyright: 2026 ZhaoJun233
- Use: the fixed source was reviewed for password login, the absence of an
  independent `/checkin` route, login-triggered daily quota, session-cookie
  handling, and strict `checked_in` semantics.

### agentrouter-magpie-plugin domestic variant

- Source: `nijiong/agentrouter-magpie-plugin`
- Fixed commit reviewed: `ad19fc09e7e2182af9dc063053227686d5dc127c`
- License: MIT
- Copyright: 2026 ZhaoJun233, with modifications by nijiong
- Use: the fixed source was compared for the same
  `POST /api/user/login` contract, `username` / `password` JSON body,
  `Set-Cookie: session` handling, `quota` / `used_quota` fields, and
  `checked_in` interpretation.

## Contract Findings

Both fixed sources call `POST /api/user/login` with a JSON body containing
`username` and `password`. The reviewed source treats the response's
`Set-Cookie: session=...` value as the authenticated session. It does not read
a JSON `token` field from the login body.

`data.checked_in=true` means the site reports that this login added the day's
quota. `data.checked_in=false` means the login was accepted but no new quota
was reported. A missing or non-boolean value is not treated as proof by the
stricter reviewed implementation.

Neither fixed source defines an independent `/api/user/checkin` route for
ordinary accounts. The daily credit is triggered by login. This local script
therefore does not issue a separate `/checkin` request.

The local implementation records the login response's `checked_in` value as
the post-login state. When `checked_in=true`, the pre-login state is recorded
as false because the server's documented meaning is that the request added the
day's quota. When `checked_in=false`, the pre-login value remains null because
username/password alone do not provide a side-effect-free pre-login status
read.

## Third-Party MIT License

MIT License

Copyright (c) 2026 ZhaoJun233

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Runtime Dependencies

- `requests` is installed from PyPI under its own license.

## Project License

The local implementation is released under the MIT License reproduced in
[`LICENSE`](LICENSE).
