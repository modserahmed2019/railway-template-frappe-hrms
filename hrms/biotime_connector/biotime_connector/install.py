from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def get_custom_fields():
    return {
        "Employee Checkin": [
            {
                "fieldname": "biotime_transaction_id",
                "fieldtype": "Data",
                "label": "BioTime Transaction ID",
                "insert_after": "device_id",
                "read_only": 1,
                "no_copy": 1,
            },
            {
                "fieldname": "biotime_punch_state",
                "fieldtype": "Data",
                "label": "BioTime Punch State",
                "insert_after": "biotime_transaction_id",
                "read_only": 1,
                "no_copy": 1,
            },
            {
                "fieldname": "biotime_terminal_sn",
                "fieldtype": "Data",
                "label": "BioTime Terminal SN",
                "insert_after": "biotime_punch_state",
                "read_only": 1,
                "no_copy": 1,
            },
            {
                "fieldname": "biotime_terminal_alias",
                "fieldtype": "Data",
                "label": "BioTime Terminal",
                "insert_after": "biotime_terminal_sn",
                "read_only": 1,
                "no_copy": 1,
            },
            {
                "fieldname": "biotime_area_alias",
                "fieldtype": "Data",
                "label": "BioTime Area",
                "insert_after": "biotime_terminal_alias",
                "read_only": 1,
                "no_copy": 1,
            },
        ]
    }


def ensure_custom_fields():
    create_custom_fields(get_custom_fields(), ignore_validate=True)


def after_install():
    ensure_custom_fields()


def after_migrate():
    ensure_custom_fields()
