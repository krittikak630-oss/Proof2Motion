# Security

## What is protected
| Risk | Mitigation (see `backend/app/`) |
| --- | --- |
| API key leaks | Key lives only in server-side `.env` / environment variables. It is never sent to the browser, never logged, and `.env` is git-ignored. |
| Malicious uploads | Allow-list of TXT/MD/PDF, `%PDF-` signature check, binary-in-text check, max 5 files, 5 MB each, PDF page cap, request-size cap (`extract.py`, `main.py`). Files are processed in memory and never written to disk. |
| Abuse / cost | Per-IP rate limit (default 8 analyses per minute) with `Retry-After` (`security.py`). |
| Prompt injection | Evidence is fenced inside `<evidence>` tags, the model is told to treat it as data, and the closing tag is neutralised inside uploads (`prompts.py`). Output is validated against a strict schema (`schemas.py`). |
| Hallucinated proof | Every quote is checked word for word against the uploaded text. Unverified quotes are flagged and unproven "supported" claims are downgraded (`verify.py`). |
| XSS | React escapes all output; strict Content-Security-Policy (`script-src 'self'`); no `dangerouslySetInnerHTML`. |
| Clickjacking, sniffing | `X-Frame-Options: DENY`, `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`. |
| Path traversal | Static files are resolved and must stay inside `frontend/dist` (tested). |
| Information leaks | Unexpected errors return a short reference id; details go to server logs only. API docs are disabled when `ENVIRONMENT=production`. |
| Transport | HSTS is sent in production over HTTPS. Terminate TLS at the Cloudways/DigitalOcean proxy. |

Tests for all of the above run with `cd backend && python -m pytest`.

## Known limits
- The rate limiter is in memory (per process). Use a shared store such as Redis if you scale to several servers.
- There are no user accounts. Add authentication before exposing this to untrusted public traffic at scale.
- Uploaded text is sent to the Gemini API for analysis. Do not upload confidential documents.

## Reporting a vulnerability
Open a private security advisory on the GitHub repository, or email the maintainers listed there.
