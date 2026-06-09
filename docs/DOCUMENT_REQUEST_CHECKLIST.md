# Document Request Checklist and Agency Document Delivery

## Two document directions

The system treats documents differently depending on who provides them:

| Source type | Who provides | Client sees |
|-------------|--------------|-------------|
| `client_required` | Client uploads own documents | Section **Нужно от вас** |
| `agency_prepared` | Agency prepares and shares later | Section **Готовит агентство** |

Do not merge these into a single generic checklist.

## Client-provided categories

Examples:

- `international_passport` — Загранпаспорт
- `photo` — Фото
- `bank_statement` — Выписка из банка
- `insurance_own` — Своя страховка (optional; client may report no insurance)
- `employment_certificate`, `student_certificate`
- `marriage_certificate`, `child_birth_certificate`, `previous_visas`
- `other_client_document`

Statuses:

- `requested` → Ожидаем от вас
- `uploaded_by_client` / `received_by_manager` → Загружено, менеджер проверяет
- `approved` → Принято
- `rejected` → Нужно заменить
- `not_needed` → Не требуется

## Agency-prepared categories

Examples:

- `hotel_booking`, `transport_booking`, `invitation`, `travel_plan`
- `filled_application_form`, `appointment_confirmation`
- `insurance_agency_prepared`, `cover_letter`, `other_agency_document`

Statuses:

- `planned` → Запланировано
- `preparing_by_agency` → Готовит агентство
- `ready_for_client` → Готово
- `shared_with_client` → Передано клиенту
- `not_needed` → Не требуется

## Manager flow (Telegram bot)

Menu action: **📎 Документы по заявке**

1. Enter case ID.
2. Choose action:
   - show documents for case
   - request client document from template
   - add agency-prepared item
   - change document status
   - leave manager comment
3. After client request, bot notifies client with safe metadata only:

   ```text
   Менеджер запросил документы.
   Откройте личный кабинет → Документы.
   ```

4. When agency document becomes `ready_for_client`, client receives:

   ```text
   Документ от агентства готов: <title>.
   Откройте личный кабинет → Документы.
   ```

Admin HTTP API is **not** exposed publicly in this MVP. Manager actions go through the existing bot handlers calling `DocumentRepository` directly.

## Client Mini App flow

Route: `/documents`

Bottom navigation tab: **Документы** (settings remain at `/settings`, linked from home header).

API:

- `GET /api/case/current/documents`
- `GET /api/case/current/documents/summary`
- `POST /api/case/current/documents/{document_id}/upload`
- `POST /api/case/current/documents/{document_id}/comment`
- `GET /api/case/current/documents/{document_id}/download` (agency docs only)

Cabinet summary includes a documents block with counts only (no filenames).

## Upload behavior (MVP)

Upload is gated by env:

```env
DOCUMENT_UPLOADS_ENABLED=false
DOCUMENT_STORAGE_DIR=./storage/documents
DOCUMENT_MAX_FILE_MB=15
```

When disabled:

- upload endpoint returns `501`
- Mini App shows: *Загрузка файлов будет доступна позже. Свяжитесь с менеджером.*

When enabled:

- upload only through authenticated Mini App API
- allowed types: JPEG, PNG, PDF
- files stored locally under `apps/telegram-bot/storage/documents/{case_id}/{document_item_id}/{file_id}`
- database stores metadata only
- no public direct file URLs
- client cannot re-download own uploads in MVP (manager review side)

## Sensitive data safety

**Never** send through Telegram chat:

- passport scans
- photos
- bank statements
- document file contents
- unauthorized download links

Safe manager notification after client upload:

```text
Клиент загрузил документ.
Кейс: VISA-CASE-2026-000123
Документ: Загранпаспорт
Статус: uploaded_by_client
```

## Production storage requirements

Local filesystem storage is for development/MVP only. Production requires:

- secure object storage (S3-compatible or equivalent)
- encryption at rest
- access control and authorization on every download
- backups and retention policy
- audit logging for document access

## Known limitations

- no manager agency file upload through bot in this PR (status + comment only)
- no PDF generation
- no online payments
- no visa-center booking integration
- no guarantee of visa approval or slot availability

## Next package

**PR-VISA-07F** — Secure Document Upload Hardening + Manager Document Review
