# BioTime Connector

Frappe HR integration for pulling employee punch transactions from BioTime Cloud and creating `Employee Checkin` records.

Configuration is read from environment variables:

- `BIOTIME_BASE_URL`
- `BIOTIME_COMPANY`
- `BIOTIME_EMAIL`
- `BIOTIME_PASSWORD`

The connector intentionally does not guess BioTime punch-state meanings. It stores the raw punch state in a custom field and leaves `Employee Checkin.log_type` empty so Frappe HR can apply the configured Shift Type logic.
