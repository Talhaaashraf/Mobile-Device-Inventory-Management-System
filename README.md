# Folio3 Mobile Device IMS

Full-stack inventory tracker for company phones, tablets, and smartwatches.

## Stack

- **Frontend:** React (Vite) + React Router + Axios
- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Database:** SQLite (local)
- **Auth:** JWT access + refresh tokens with RBAC (`admin`, `manager`, `viewer`)
- **Runtime:** Local development with `start-local.bat`

## Quick start (Windows)

Use the provided local startup helper or start the backend and frontend manually.

### Local startup script

Double-click `start-local.bat` or run it from PowerShell:

```powershell
cd device-inventory
start-local.bat
```

### Manual startup

```powershell
# Terminal 1 — backend (SQLite)
cd backend
set DATABASE_URL=sqlite:///./device_inventory.db
set CORS_ORIGINS=http://localhost:3000
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
set VITE_API_URL=http://localhost:8000
npm run dev -- --port 3000 --host
```

Then open http://localhost:3000

## Import devices from CSV

1. Sign in as **admin** or **manager**
2. Open **Devices**
3. Click **CSV template** (or use `sample-devices.csv` in the project root)
4. Fill your rows, then click **Import CSV**

Required columns:

`device_name,device_nickname,device_type,os_type,os_version,is_cellular,serial_number,mac_address,company`

Optional: `imei_number`, `status`, `audit_status`, `resident_location`, `division`, `issued_to`, `project_manager`, `project_name`, `date_of_return`, `purchase_date` (YYYY-MM-DD), `assigned_user_email`

API: `POST /api/devices/import` (multipart form field `file`)

## Seed accounts

| Role    | Email                 | Password      |
|---------|-----------------------|---------------|
| Admin   | admin@company.com     | Admin123!     |
| Manager | manager@company.com   | Manager123!   |
| Viewer  | viewer@company.com    | Viewer123!    |

## Local development (optional)

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
set DATABASE_URL=sqlite:///./device_inventory.db
set CORS_ORIGINS=http://localhost:3000
set SEED_ON_STARTUP=true
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
set VITE_API_URL=http://localhost:8000
npm run dev
```

## Roles

| Role    | Capabilities                                      |
|---------|---------------------------------------------------|
| Admin   | Full access including user admin and hard delete  |
| Manager | Create/edit/assign devices, view reports          |
| Viewer  | Read-only inventory and dashboard                 |

## Main API routes

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET|POST|PATCH /api/users` (admin)
- `GET /api/users/assignees` (admin/manager)
- `GET|POST /api/devices`
- `GET|PATCH|DELETE /api/devices/{id}`
- `GET /api/devices/{id}/history`
- `GET /api/dashboard/summary`

## Notes

- IMEI is required only when `is_cellular` is true (15 digits).
- MAC addresses must match `XX:XX:XX:XX:XX:XX` and are stored uppercase.
- Assignment history is written whenever `assigned_user_id` changes.
