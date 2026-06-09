# Status Timeline and Personal Cabinet

## API sources

| Endpoint | Purpose |
|----------|---------|
| `GET /api/cabinet/summary` | Dashboard: access, case, applicants progress, appointment, next action |
| `GET /api/case/current/timeline` | Full status timeline with step states |

Frontend types: `CabinetSummary`, `CaseTimelineResponse`, `TimelineStep`, `NextAction`.

Mini App methods: `api.getCabinetSummary()`, `api.getCaseTimeline()`.

## Personal cabinet structure

Home dashboard cards:

1. **Access** — active/inactive, CTA back to bot when inactive
2. **Case** — country, city, provider, applicants count, human status label
3. **Next action** — label + link from backend (`next_action.href`)
4. **Applicants** — `Заполнено: X из Y` + progress bar
5. **Appointment** — no options / options available / selected / confirmed
6. **Manager hint** — legal-safe copy, no guarantees
7. **Timeline preview** — 4–6 steps around current stage, link to `/status`

## Timeline states

| State | UI meaning |
|-------|------------|
| `done` | Completed step |
| `current` | Current stage |
| `locked` | Future step |
| `warning` | Cancelled or needs attention |

Component: `StatusTimeline` accepts `steps: TimelineStep[]` from backend only. No frontend status mapping.

State labels: Выполнено / Сейчас / Ожидает / Требует внимания.

## Next action routing

Examples from backend:

| Label | Typical href |
|-------|--------------|
| Заполните анкеты заявителей | `/applicants` |
| Выберите страну и город подачи | `/case` |
| Ожидайте проверки менеджера | `/status` |
| Выберите удобную дату | `/appointment` |

When no access or no case, top-level `summary.next_action` is used.

## Appointment display

| State | Copy |
|-------|------|
| No options | Manager is searching dates manually |
| Options sent | Choose a convenient date |
| Selected | Awaiting manager confirmation |
| Confirmed | Appointment confirmed with date, city, provider |

## Applicant progress

List cards show only safe fields: name (if entered), position, completion percent, status label (`заполнено` / `черновик`). No passport, address, or birth place on dashboard or list views.

## Sensitive data exclusion

Cabinet summary and timeline APIs must not include:

- passport numbers and dates
- birth place
- residence address
- bank data
- full applicant profile payloads

Dashboard, timeline, and Telegram notifications use aggregated or metadata-only data.

## Legal-safe wording

Allowed:

- Менеджер проверит данные и сообщит следующие шаги.
- Доступность дат зависит от внешних систем.
- Финальное решение по визе принимает консульство или уполномоченный визовый орган.

Not used:

- гарантируем запись / визу
- точно запишем
