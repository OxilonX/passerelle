# Passerelle — Project Overview

## Objective

Passerelle is a university internship-management application. It is intended to centralize the records involved in the internship process: students, host companies, academic and company supervisors, and the internships that connect them, plus user accounts for authentication.

The name is declared in `pyproject.toml` as `passerelle` ("gateway/bridge"), described there as a *University internship-management app*. The login screen presents it as an *Internship Management System* for managing students, companies, and internships.

The current implementation is an early scaffold:

- The SQLite schema and ORM models are defined.
- Login and registration work through a NiceGUI page.
- Service-layer CRUD/validation logic exists for all domain entities.
- The dashboard is a placeholder; CRUD UI pages for students, companies, supervisors, and internships are not yet implemented.
- There are no tests yet, no migration system, and no authorization roles.

## App Structure

```text
passerelle/
├── main.py                  # Entry point: registers pages, creates tables, starts NiceGUI
├── app/
│   ├── database.py          # SQLite engine, FK pragma, create_all(), get_session()
│   ├── models.py            # SQLModel tables and enums (authoritative schema)
│   ├── pages/               # NiceGUI UI layer
│   │   ├── login.py         # Login/register page, password hashing
│   │   ├── theme.py         # Dark theme color constants
│   │   ├── students.py      # Placeholder (empty)
│   │   ├── companies.py     # Placeholder (empty)
│   │   └── internships.py   # Placeholder (empty)
│   └── services/            # Business logic and DB queries
│       ├── user.py          # Create/get/list users
│       ├── login.py         # Password verification and authentication
│       ├── students.py      # StudentService (add, find, update, delete)
│       ├── companies.py     # Company CRUD and search
│       ├── supervisor.py    # Supervisor CRUD, filtering, company rule
│       └── internships.py   # Internship CRUD, date and FK validation
├── tests/
│   ├── unit/                # Empty (.gitkeep)
│   └── integration/         # Empty (.gitkeep)
├── pyproject.toml           # Dependencies and pytest config
└── internships.db           # Local SQLite file (gitignored)
```

### Layers

1. **Entry point** — `main.py` defines `@ui.page("/")` (login) and `@ui.page("/dashboard")` (placeholder), calls `create_db_and_tables()`, then `ui.run(title="Passerelle", reload=False)`.
2. **Pages (UI)** — Declarative NiceGUI components. Only `login.py` is implemented. It uses `theme.py` constants and the user/login services.
3. **Services** — Domain logic and queries over a SQLModel `Session`. Most functions accept an optional session; if none is given they open and close their own. `StudentService` uses a session factory and is exposed as a module-level singleton.
4. **Models** — Five `SQLModel(table=True)` classes and two enums in `app/models.py`.
5. **Database** — `app/database.py` creates the engine for `sqlite:///internships.db` with `check_same_thread=False`, enables `PRAGMA foreign_keys=ON` on every connection, creates tables with `SQLModel.metadata.create_all(engine)`, and provides `get_session()`.

### Runtime flow

1. Opening `/` builds the login/register card.
2. Registration hashes the password with PBKDF2-HMAC-SHA256 (16-byte random salt, 100,000 iterations, stored as `salt$digest`) and creates a `User`.
3. Login calls the login service, which verifies the hash (with a plaintext fallback) and authenticates the user.
4. On success the app navigates to `/dashboard`, which currently only shows a static label.

### Stack

- Python 3.12 (`pyproject.toml`, `.python-version`)
- NiceGUI 4.0.0 (UI, routing, server)
- SQLModel 0.0.50 / SQLAlchemy 2.1.8 (ORM)
- SQLite (local `internships.db` file)
- bcrypt 5.0.0 is declared but unused; passwords use PBKDF2 instead
- pytest 9.2.0 (configured, no tests written)

### Run commands

```bash
uv sync
uv run python main.py
uv run pytest
```

## Database Model

The schema lives in code at `app/models.py`; the local `internships.db` file is gitignored. There are no migrations — `create_all()` creates missing tables but does not alter existing ones, so model changes require recreating the database (or a future migration tool). Foreign keys are actively enforced by SQLite because `PRAGMA foreign_keys=ON` is set per connection.

### Enums

- **`InternshipStatus`** — `PENDING` (`"pending"`), `IN_PROGRESS` (`"in progress"`), `COMPLETED` (`"completed"`). Stored as `VARCHAR(11)`; no DB-level check constraint.
- **`SupervisorType`** — `ACADEMIC` (`"academic"`), `COMPANY` (`"company"`). Stored as `VARCHAR(8)`; no DB-level check constraint.

### Tables

#### `student`

| Field | Type | Notes |
|---|---|---|
| `id` | `int` | Primary key |
| `registration_number` | `str` | Required, unique, indexed |
| `last_name` | `str` | Required |
| `first_name` | `str` | Required |
| `date_of_birth` | `date` | Required |
| `address` | `str` | Required |
| `email` | `str` | Required, not unique |

A student can have many internships. `StudentService` validates required fields and duplicate registration numbers, translates `IntegrityError` into `ValueError`, and manually deletes related internships before deleting a student (the FK also has `ON DELETE CASCADE`).

#### `company`

| Field | Type | Notes |
|---|---|---|
| `id` | `int` | Primary key |
| `identifier` | `str` | Required, unique, indexed |
| `company_name` | `str` | Required, indexed (non-unique) |
| `address` | `str` | Required |
| `industry` | `str` | Required |
| `contact` | `str` | Required |

A company can have many internships and many supervisors. Services support add, search by identifier or name substring, get by identifier, list, update, and delete. Deleting a company with dependent rows is blocked by SQLite because those FKs use `NO ACTION`.

#### `supervisor`

| Field | Type | Notes |
|---|---|---|
| `id` | `int` | Primary key |
| `last_name` | `str` | Required |
| `first_name` | `str` | Required |
| `supervisor_type` | `SupervisorType` | Required: `academic` or `company` |
| `company_id` | `int \| None` | Nullable FK to `company.id` |

A supervisor can be referenced by internships in two roles (academic and company). Application rules require a `company_id` when the type is `company` and verify that the company exists. There is no check that an internship's academic supervisor is actually `academic` (or its company supervisor is actually `company`).

#### `internship`

Table-level constraint: `CHECK (end_date >= start_date)` named `ck_dates`.

| Field | Type | Notes |
|---|---|---|
| `id` | `int` | Primary key |
| `topic` | `str` | Required |
| `start_date` | `date` | Required |
| `end_date` | `date` | Required |
| `description` | `str` | Required |
| `status` | `InternshipStatus` | Required, indexed, Python default `PENDING` (no SQL default) |
| `student_id` | `int` | Required FK to `student.id`, `ON DELETE CASCADE` |
| `company_id` | `int` | Required FK to `company.id` |
| `academic_supervisor_id` | `int` | Required FK to `supervisor.id` |
| `company_supervisor_id` | `int` | Required FK to `supervisor.id` |

Services validate dates (including the check constraint) and verify that all referenced student, company, and supervisor IDs exist on insert and on updates. Search supports filtering by internship ID, student ID, and/or status.

#### `user`

| Field | Type | Notes |
|---|---|---|
| `id` | `int` | Primary key |
| `username` | `str` | Required, unique |
| `password_hash` | `str` | Required, stored as `salt$digest` (PBKDF2) |

Standalone table: no relationship to student, supervisor, or company, and no role/authorization table.

### Relationships

| Parent | Child | Foreign key | On delete |
|---|---|---|---|
| `student` | `internship` | `internship.student_id` | `CASCADE` |
| `company` | `internship` | `internship.company_id` | `NO ACTION` |
| `company` | `supervisor` | `supervisor.company_id` | `NO ACTION` (nullable) |
| `supervisor` | `internship` | `internship.academic_supervisor_id` | `NO ACTION` |
| `supervisor` | `internship` | `internship.company_supervisor_id` | `NO ACTION` |
| — | `user` | — | Standalone |

There are no SQLModel `Relationship(...)` attributes; navigation is done manually through ID queries in the service layer.

### Indexes

- `ix_student_registration_number` — unique
- `ix_company_identifier` — unique
- `ix_company_company_name` — non-unique
- `ix_internship_status` — non-unique
- `sqlite_autoindex_user_1` — unique (`user.username`)

## Current Limitations

- No CRUD UI pages for domain entities; only login and a placeholder dashboard.
- No authenticated session handling, protected routes, or user roles.
- `User` is not linked to any student/company/supervisor identity.
- No migrations, seed data, or tests.
- Enum values are enforced in Python, not by SQLite check constraints.
