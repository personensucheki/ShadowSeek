# Monitoring & Logging für ShadowSeek

## Sentry (Error-Tracking)
- Aktiviere Sentry, indem du die Umgebungsvariable `SENTRY_DSN` setzt:
  
  ```sh
  export SENTRY_DSN="https://<key>@o123456.ingest.sentry.io/123456"
  export SENTRY_ENV=production
  export SENTRY_TRACES_SAMPLE_RATE=0.1
  ```
- Sentry überwacht Fehler und Performance automatisch.

## Prometheus (Metriken)
- Prometheus-Exporter ist per Default aktiv (Umgebungsvariable `PROMETHEUS_ENABLED=1`).
- Der /metrics-Endpoint liefert Prometheus-kompatible Metriken.
- Beispiel für Prometheus scrape config:
  ```yaml
  scrape_configs:
    - job_name: 'shadowseek'
      static_configs:
        - targets: ['localhost:10000']
  ```

## Hinweise
- Beide Systeme sind optional und können unabhängig voneinander aktiviert werden.
- Für Produktion dringend empfohlen!
