app_name = "biotime_connector"
app_title = "BioTime Connector"
app_publisher = "Etihad"
app_description = "BioTime Cloud to Frappe HR Employee Checkin connector"
app_email = "it-manager@etihad.sa"
app_license = "MIT"
required_apps = ["hrms"]

after_install = "biotime_connector.install.after_install"
after_migrate = "biotime_connector.install.after_migrate"

scheduler_events = {
    "cron": {
        "*/5 * * * *": [
            "biotime_connector.sync.sync_recent",
        ]
    }
}
