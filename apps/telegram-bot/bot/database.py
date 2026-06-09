from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  telegram_id INTEGER NOT NULL UNIQUE,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  patronymic TEXT,
  birth_date TEXT,
  citizenship TEXT,
  current_location TEXT,
  phone TEXT,
  email TEXT,
  consent_accepted_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,
  public_number TEXT NOT NULL UNIQUE,
  user_id TEXT NOT NULL,
  country_code TEXT NOT NULL,
  country_name_ru TEXT NOT NULL,
  submission_city TEXT NOT NULL,
  provider TEXT,
  visa_purpose TEXT NOT NULL,
  time_window_code TEXT NOT NULL,
  applicants_count INTEGER NOT NULL,
  base_price_rub INTEGER NOT NULL,
  additional_applicants_price_rub INTEGER NOT NULL,
  discount_rub INTEGER NOT NULL,
  total_price_rub INTEGER NOT NULL,
  promo_code TEXT,
  access_key_code TEXT,
  access_key_id TEXT,
  payment_status TEXT NOT NULL,
  order_status TEXT NOT NULL,
  requires_manager_review INTEGER NOT NULL,
  manager_note TEXT,
  user_comment TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS applicants (
  id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL,
  last_name TEXT NOT NULL,
  first_name TEXT NOT NULL,
  patronymic TEXT,
  birth_date TEXT NOT NULL,
  citizenship TEXT NOT NULL,
  current_location TEXT,
  relationship TEXT,
  passport_number_encrypted TEXT,
  passport_expiry_date TEXT
);
CREATE TABLE IF NOT EXISTS payments (
  id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  provider_payment_id TEXT,
  amount_rub INTEGER NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  paid_at TEXT
);
CREATE TABLE IF NOT EXISTS promo_codes (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  type TEXT NOT NULL,
  value INTEGER NOT NULL,
  max_uses INTEGER NOT NULL,
  used_count INTEGER NOT NULL,
  active INTEGER NOT NULL,
  expires_at TEXT,
  created_by_admin_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  country_codes TEXT,
  time_window_codes TEXT,
  note TEXT
);
CREATE TABLE IF NOT EXISTS audit_log (
  id TEXT PRIMARY KEY,
  actor_type TEXT NOT NULL,
  actor_id TEXT,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  action TEXT NOT NULL,
  before TEXT,
  after TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS access_keys (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL,
  max_uses INTEGER NOT NULL,
  used_count INTEGER NOT NULL,
  bound_user_id TEXT,
  bound_telegram_id INTEGER,
  country_codes TEXT,
  service_type TEXT,
  max_applicants INTEGER,
  expires_at TEXT,
  created_by_admin_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  note TEXT
);
CREATE TABLE IF NOT EXISTS support_requests (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  telegram_id INTEGER NOT NULL,
  username TEXT,
  message TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS visa_cases (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  telegram_id INTEGER NOT NULL,
  access_key_id TEXT,
  access_key_code TEXT,
  status TEXT NOT NULL,
  applicants_count INTEGER NOT NULL,
  desired_country_code TEXT,
  desired_country_name_ru TEXT,
  preferred_submission_city TEXT,
  submission_provider TEXT,
  submission_provider_type TEXT,
  submission_jurisdiction TEXT,
  submission_verification_status TEXT,
  travel_purpose TEXT,
  approximate_travel_start_date TEXT,
  approximate_travel_end_date TEXT,
  client_comment TEXT,
  submitted_at TEXT,
  manager_reviewed_at TEXT,
  selected_slot_option_id TEXT,
  selected_appointment_date TEXT,
  selected_appointment_time TEXT,
  selected_appointment_city TEXT,
  selected_appointment_provider TEXT,
  appointment_confirmed_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS appointment_slot_offers (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL,
  created_by_admin_id INTEGER NOT NULL,
  status TEXT NOT NULL,
  message TEXT,
  expires_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS appointment_slot_options (
  id TEXT PRIMARY KEY,
  offer_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  option_date TEXT NOT NULL,
  option_time TEXT NOT NULL,
  city TEXT,
  provider TEXT,
  address TEXT,
  comment TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS applicant_profiles (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  telegram_id INTEGER NOT NULL,
  case_id TEXT,
  position INTEGER NOT NULL,
  role TEXT,
  status TEXT NOT NULL,
  completion_percent INTEGER NOT NULL,
  last_name_latin TEXT,
  first_name_latin TEXT,
  last_name_cyrillic TEXT,
  first_name_cyrillic TEXT,
  patronymic TEXT,
  birth_date TEXT,
  birth_place TEXT,
  citizenship TEXT,
  gender TEXT,
  marital_status TEXT,
  phone TEXT,
  email TEXT,
  residence_country TEXT,
  residence_city TEXT,
  residence_address TEXT,
  postal_code TEXT,
  passport_number TEXT,
  passport_issue_date TEXT,
  passport_expiry_date TEXT,
  passport_issuing_authority TEXT,
  passport_issuing_country TEXT,
  desired_country_code TEXT,
  desired_country_name_ru TEXT,
  travel_purpose TEXT,
  approximate_travel_dates TEXT,
  entries_count TEXT,
  preferred_submission_city TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS document_items (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL,
  applicant_id TEXT,
  source_type TEXT NOT NULL,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL,
  required INTEGER NOT NULL,
  visible_to_client INTEGER NOT NULL,
  requested_by_admin_id INTEGER,
  requested_at TEXT,
  due_date TEXT,
  uploaded_by TEXT,
  uploaded_at TEXT,
  reviewed_by_admin_id INTEGER,
  reviewed_at TEXT,
  manager_comment TEXT,
  client_comment TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS document_files (
  id TEXT PRIMARY KEY,
  document_item_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  applicant_id TEXT,
  uploaded_by TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  mime_type TEXT,
  size_bytes INTEGER,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""

ALTERS = (
    "ALTER TABLE orders ADD COLUMN access_key_code TEXT",
    "ALTER TABLE orders ADD COLUMN access_key_id TEXT",
    "ALTER TABLE visa_cases ADD COLUMN submission_provider TEXT",
    "ALTER TABLE visa_cases ADD COLUMN submission_provider_type TEXT",
    "ALTER TABLE visa_cases ADD COLUMN submission_jurisdiction TEXT",
    "ALTER TABLE visa_cases ADD COLUMN submission_verification_status TEXT",
    "ALTER TABLE visa_cases ADD COLUMN travel_purpose TEXT",
    "ALTER TABLE visa_cases ADD COLUMN approximate_travel_start_date TEXT",
    "ALTER TABLE visa_cases ADD COLUMN approximate_travel_end_date TEXT",
    "ALTER TABLE visa_cases ADD COLUMN client_comment TEXT",
    "ALTER TABLE visa_cases ADD COLUMN submitted_at TEXT",
    "ALTER TABLE visa_cases ADD COLUMN manager_reviewed_at TEXT",
    "ALTER TABLE visa_cases ADD COLUMN selected_slot_option_id TEXT",
    "ALTER TABLE visa_cases ADD COLUMN selected_appointment_date TEXT",
    "ALTER TABLE visa_cases ADD COLUMN selected_appointment_time TEXT",
    "ALTER TABLE visa_cases ADD COLUMN selected_appointment_city TEXT",
    "ALTER TABLE visa_cases ADD COLUMN selected_appointment_provider TEXT",
    "ALTER TABLE visa_cases ADD COLUMN appointment_confirmed_at TEXT",
)


def sqlite_path_from_url(database_url: str) -> Path:
    prefix = "sqlite+aiosqlite:///"
    raw = database_url[len(prefix) :] if database_url.startswith(prefix) else "visa_bot.db"
    return Path(raw)


def init_db(database_url: str) -> None:
    path = sqlite_path_from_url(database_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.executescript(SCHEMA)
        for statement in ALTERS:
            try:
                connection.execute(statement)
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        connection.commit()
    finally:
        connection.close()
