FROM docker.io/frappe/erpnext:v16.31.1@sha256:dba34b89f11e22e14cfc05f6846ff39a223187bf7dfc63266565d646f1569674

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=frappe:frappe biotime_connector /home/frappe/frappe-bench/apps/biotime_connector

USER frappe
WORKDIR /home/frappe/frappe-bench
RUN bench get-app --branch v16.16.0 https://github.com/frappe/hrms \
    && ./env/bin/pip install -e apps/biotime_connector \
    && (grep -Fxq 'biotime_connector' sites/apps.txt || echo 'biotime_connector' >> sites/apps.txt) \
    && bench build \
    && grep -Fq '"website.bundle.css"' sites/assets/assets.json \
    && grep -Fq '"erpnext-web.bundle.css"' sites/assets/assets.json \
    && grep -Fq '"hrms.bundle.css"' sites/assets/assets.json \
    && rm -rf /home/frappe/frappe-bench/assets \
    && cp -r /home/frappe/frappe-bench/sites/assets /home/frappe/frappe-bench/assets

USER root
COPY entrypoint.sh /usr/local/bin/hrms-entrypoint
COPY supervisord.conf /etc/supervisor/conf.d/hrms.conf
RUN chmod 755 /usr/local/bin/hrms-entrypoint

ENV PORT=8080
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/hrms-entrypoint"]
