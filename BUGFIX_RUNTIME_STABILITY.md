# BUGFIX_RUNTIME_STABILITY.md

## Feed-API Fehler (Ursache & Fix)
- Ursache: Fehler in Datenbankabfrage, Serialisierung oder fehlende Demo-/Userdaten führten zu unkontrolliertem 500-Fehler.
- Fix: Komplette /api/feed-Route mit try/except abgesichert, Logging ergänzt, Response immer im Schema {"success": true, "data": [...]} oder {"success": false, "error": {...}}.
- Upload- und UserPosts-API ebenfalls auf konsistente Fehlerbehandlung und Response-Format umgestellt.

## Provider-Status Fehler (Ursache & Fix)
- Ursache: Einzelne Provider (z.B. fehlende ENV, Importfehler, API-Timeout) konnten die gesamte /api/providers/status-Route crashen.
- Fix: Jeder Provider wird einzeln mit try/except geprüft, Fehler werden geloggt, Response enthält für jeden Provider provider_status (ok|error|disabled) und Fehlerdetails, aber keine Exception nach außen.

## Geänderte Dateien
- app/routes/feed.py
- app/routes/provider_status.py
- app/__init__.py

## Ergänzte Guards
- try/except um alle kritischen API-Routen
- Logging aller Exceptions
- api_success/api_error als Standard für alle API-Responses
- Globaler Error-Handler für konsistente Fehler-Responses

## Fehlerabfang jetzt
- Kein 500 mehr ohne kontrollierte JSON-Response
- Fehler werden geloggt, aber nicht ins Frontend durchgereicht
- Alle APIs liefern konsistente Struktur: {"success": true, "data": ...} oder {"success": false, "error": ...}

## media_posts Schema-Drift & Reparatur (April 2026)
- Root-Cause: Die Tabelle `media_posts` fehlte in der produktiven Datenbank trotz Alembic-Head, da Migrationen nicht korrekt angewendet wurden (Schema-Drift).
- Reparaturmaßnahme: Gezielte Reparaturmigration erstellt, die Tabelle und alle fehlenden Spalten ergänzt. Migrationen angewendet, ORM- und DB-Schema synchronisiert.
- Test: Erfolgreicher Insert eines Testposts (user_id=1, "Testpost") per Flask-Shell.
- Feed-API-Retest: /api/feed, /api/feed?limit=1, /api/u/ADMIN/posts liefern jetzt korrekte Datenobjekte, success=true, und enthalten den Testpost.
- Demo-Branch: /api/feed?demo=1 liefert konsistente JSON-Antwort, kein 500-Fehler.
- Health-Check: /health liefert {"status": "ok"}.
- Mapping: Alle Felder (id, media_url, user info, caption, created_at, etc.) sind im Response enthalten und passen zum Frontend.
- Abschluss: Fehlerursache dokumentiert, Fix angewendet, Endpunkte erfolgreich getestet.
