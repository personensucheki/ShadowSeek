# Gunicorn/WSGI Deployment für ShadowSeek

**Empfohlen für Produktion:**

1. **Installiere alle Abhängigkeiten:**
   
   ```sh
   pip install -r requirements.txt
   ```

2. **Starte die App mit Gunicorn:**
   
   ```sh
   gunicorn -w 4 -b 0.0.0.0:10000 app:app
   ```
   - `-w 4` = 4 Worker-Prozesse (anpassen je nach CPU)
   - `-b` = Bind-Adresse und Port
   - `app:app` = Modul:Flask-App-Objekt

3. **Optional: Eigene Gunicorn-Konfiguration:**
   
   Erstelle eine Datei `gunicorn.conf.py` im Projektverzeichnis, z.B.:
   
   ```python
   bind = '0.0.0.0:10000'
   workers = 4
   timeout = 60
   accesslog = '-'
   errorlog = '-'
   loglevel = 'info'
   preload_app = True
   ```
   
   Dann starten mit:
   ```sh
   gunicorn -c gunicorn.conf.py app:app
   ```

4. **Hinweis:**
   - Für Reverse Proxy (z.B. Nginx) Gunicorn hinter Nginx betreiben.
   - Flask-Dev-Server (`python app.py`) ist nur für Entwicklung gedacht!
