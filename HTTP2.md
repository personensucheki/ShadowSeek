# HTTP/2 Aktivierung für ShadowSeek

HTTP/2 wird nicht direkt von Flask oder Gunicorn unterstützt, sondern vom Reverse Proxy (z.B. Nginx, Caddy, Apache). Für Produktion dringend empfohlen!

## Beispiel: Nginx als Reverse Proxy mit HTTP/2 und SSL

```
server {
    listen 443 ssl http2;
    server_name shadowseek.de;

    ssl_certificate     /etc/letsencrypt/live/shadowseek.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shadowseek.de/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location / {
        proxy_pass         http://127.0.0.1:10000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
        proxy_redirect     off;
    }

    # Optional: Static files direkt ausliefern
    location /static/ {
        alias /pfad/zum/projekt/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

server {
    listen 80;
    server_name shadowseek.de;
    return 301 https://$host$request_uri;
}
```

## Hinweise
- HTTP/2 wird durch `listen 443 ssl http2;` aktiviert.
- SSL-Zertifikat z.B. via Let's Encrypt.
- Gunicorn läuft weiterhin auf Port 10000 (ohne SSL/HTTP2).
- Für Caddy oder Apache siehe jeweilige Doku.

**Wichtig:**
- HTTP/2 ist nur mit SSL/TLS möglich.
- Reverse Proxy ist Best Practice für produktive Python-Webapps.
