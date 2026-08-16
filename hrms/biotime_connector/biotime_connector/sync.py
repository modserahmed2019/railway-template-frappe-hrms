import os
from datetime import timedelta

import frappe
import requests
from frappe.utils import get_datetime, now_datetime

TOKEN_CACHE_SECONDS = 6 * 24 * 60 * 60
DEFAULT_SYNC_DAYS = 2


def _env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _base_url():
    return _env("BIOTIME_BASE_URL").rstrip("/")


def _token_cache_key():
    return "biotime_connector:jwt:{}:{}".format(
        _env("BIOTIME_COMPANY"),
        _env("BIOTIME_EMAIL"),
    )


def clear_cached_token():
    frappe.cache().delete_value(_token_cache_key())


def get_biotime_token(force_refresh=False):
    cache_key = _token_cache_key()

    if not force_refresh:
        cached = frappe.cache().get_value(cache_key)
        if cached:
            return cached.decode() if isinstance(cached, bytes) else cached

    response = requests.post(
        f"{_base_url()}/jwt-api-token-auth/",
        json={
            "email": _env("BIOTIME_EMAIL"),
            "password": _env("BIOTIME_PASSWORD"),
            "company": _env("BIOTIME_COMPANY"),
        },
        timeout=30,
    )
    response.raise_for_status()

    token = response.json().get("token")
    if not token:
        raise RuntimeError("BioTime authentication succeeded but no JWT token was returned")

    frappe.cache().set_value(cache_key, token, expires_in_sec=TOKEN_CACHE_SECONDS)
    return token


def _get(path, params=None):
    token = get_biotime_token()
    url = f"{_base_url()}{path}"

    response = requests.get(
        url,
        headers={"Authorization": f"JWT {token}"},
        params=params,
        timeout=60,
    )

    if response.status_code == 401:
        clear_cached_token()
        token = get_biotime_token(force_refresh=True)
        response = requests.get(
            url,
            headers={"Authorization": f"JWT {token}"},
            params=params,
            timeout=60,
        )

    response.raise_for_status()
    return response.json()


def fetch_transactions(start_time, end_time, page_size=100):
    page = 1

    while True:
        payload = _get(
            "/iclock/api/transactions/",
            params={
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "page": page,
                "page_size": page_size,
            },
        )

        rows = payload.get("data") or payload.get("results") or []
        for row in rows:
            yield row

        count = int(payload.get("count") or 0)
        if not rows or page * page_size >= count:
            break

        page += 1


def find_employee(emp_code):
    return frappe.db.get_value(
        "Employee",
        {
            "attendance_device_id": str(emp_code),
            "status": "Active",
        },
        "name",
    )


def transaction_exists(row, employee, punch_time, device_id):
    transaction_id = row.get("id")

    if transaction_id and frappe.db.exists(
        "Employee Checkin",
        {"biotime_transaction_id": str(transaction_id)},
    ):
        return True

    return bool(
        frappe.db.exists(
            "Employee Checkin",
            {
                "employee": employee,
                "time": punch_time,
                "device_id": device_id,
            },
        )
    )


def import_transaction(row):
    emp_code = str(row.get("emp_code") or "").strip()
    if not emp_code:
        return "invalid"

    employee = find_employee(emp_code)
    if not employee:
        return "unmatched"

    raw_time = row.get("punch_time")
    if not raw_time:
        return "invalid"

    punch_time = get_datetime(raw_time)
    terminal_sn = str(row.get("terminal_sn") or "").strip()
    device_id = terminal_sn or "BioTimeCloud"

    if transaction_exists(row, employee, punch_time, device_id):
        return "duplicate"

    doc = frappe.get_doc(
        {
            "doctype": "Employee Checkin",
            "employee": employee,
            "time": punch_time,
            "device_id": device_id,
            "biotime_transaction_id": str(row.get("id") or ""),
            "biotime_punch_state": str(row.get("punch_state") if row.get("punch_state") is not None else ""),
            "biotime_terminal_sn": terminal_sn,
            "biotime_terminal_alias": str(row.get("terminal_alias") or ""),
            "biotime_area_alias": str(row.get("area_alias") or ""),
        }
    )

    # Do not guess BioTime punch-state meanings. log_type remains blank and
    # Frappe HR applies the configured Shift Type IN/OUT determination method.
    doc.insert(ignore_permissions=True)
    return "inserted"


def sync_now(days=DEFAULT_SYNC_DAYS):
    end_time = now_datetime()
    start_time = end_time - timedelta(days=int(days))

    stats = {
        "received": 0,
        "inserted": 0,
        "duplicate": 0,
        "unmatched": 0,
        "invalid": 0,
    }
    unmatched_codes = set()

    for row in fetch_transactions(start_time, end_time):
        stats["received"] += 1
        result = import_transaction(row)
        stats[result] += 1

        if result == "unmatched":
            unmatched_codes.add(str(row.get("emp_code") or ""))

    stats["unmatched_codes"] = sorted(code for code in unmatched_codes if code)

    frappe.logger("biotime_connector").info("BioTime sync completed: %s", stats)
    return stats


def sync_recent():
    return sync_now(days=DEFAULT_SYNC_DAYS)
