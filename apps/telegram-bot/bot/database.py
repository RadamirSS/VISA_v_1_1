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
"""


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
        connection.commit()
    finally:
        connection.close()
