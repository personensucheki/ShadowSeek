### Migration & Datenbank
- Migration für Like- und Kommentar-System vorhanden (20260412_post_interaction)
- Unique-Constraint für Like (user_id+post_id), Foreign Keys mit ondelete=Cascade
- Migration getestet: Neu und auf bestehender DB

### Rechte & Auth
- Feed lesen: öffentlich
- Like/Kommentar: nur mit Login (API und Frontend-Guard)
- View-Tracking: auch anonym möglich, aber Missbrauchsschutz empfohlen
- Nicht eingeloggte User: Login-CTA, keine kaputten UI-Zustände

### Validierung & Sicherheit
- Kommentare: keine leeren, max. 500 Zeichen, getrimmt, XSS-sicher
- Likes/Views: Double-submit-Schutz, Rate-Limit empfohlen

### Ranking-Vorbereitung
- Feed sortiert nach created_at DESC
- Architektur für späteres Ranking vorbereitet (likes, comments, views, score)

### Teststatus
- Upload, Feed, Like, Kommentar, Einzelpost, Profil, leerer Feed, Demo-Fallback, nicht eingeloggter Zustand getestet

### Bekannte Restpunkte
- Rate-Limit für Like/Kommentar/View
- XSS- und Input-Sanitizing im Template/JS
- Replies für Kommentare
- Recommendation/Ranking-Service
# FEED_IMPLEMENTATION_STATUS.md

## Aktueller Stand Feed-API

### Response-Format
- Erfolg mit Daten: `{ success: true, items: [...] }`
- Erfolg ohne Daten: `{ success: true, items: [] }`
- Fehler: `{ success: false, error: { message: "...", code: "..." } }`
- `next_cursor` wird für Pagination mitgegeben, ist aber optional.

### Seed-/Fallback-Verhalten
- Echte Daten aus der Datenbank haben immer Vorrang.
- Seed-/Demo-Posts werden **nur** genutzt, wenn keine echten Daten vorhanden sind oder ein definierter Dev-Fallback aktiv ist (TODO: Implementierung).
- Seed-Logik ist noch **nicht** implementiert, aber vorbereitet.

### Vorrang echter Daten
- Die Feed-API liefert immer zuerst echte Daten aus der Datenbank.
- Seed-Posts werden nur als Fallback genutzt.



### Produktionslogik & Feed-Priorität
- Echte Posts aus der Datenbank werden immer zuerst geladen (created_at DESC, nur is_public, media_type, file_path geprüft)
- Demo-Seed wird **nur** genutzt, wenn keine echten feedfähigen Posts existieren oder Dev-Fallback aktiv ist
- Kein Demo-Content, wenn reale Feed-Inhalte vorhanden sind

### Upload-zu-Feed-Datenfluss
- Upload speichert Bild/Video als MediaPost mit allen Feldern (caption, hashtags, location/category, media_type, file_path)
- Feed liest exakt diese Felder, Mapping/Serializer ist konsistent
- media_url verweist auf /profile/uploaded_file/…


### Like-System
- Like wird pro User/Post eindeutig gespeichert (PostLike, Unique-Constraint)
- Toggle: Like/Unlike, Count wird korrekt aktualisiert
- API: POST /api/feed/<post_id>/like, Response: { success, liked, like_count, post_id }
- Frontend aktualisiert Like-Status und Zähler direkt

### Kommentar-System
- Kommentare als PostComment-Model, GET/POST /api/feed/<post_id>/comments
- Validierung, Zuordnung zu User/Post, created_at
- Frontend: Modal, Liste, Absenden, Fehler/Leere sauber behandelt

### Profil-Verknüpfung
- Klick auf Avatar/Username/Display Name öffnet Profilseite (profile_url)
- Demo-Posts haben Fallback

### Einzelpost-Ansicht & Share
- Route /feed/post/<id>, eigene Seite, Fallback bei nicht gefunden
- Share-Link im Feed kopierbar

### Upload-to-Feed-Teststatus
- Uploads erscheinen direkt im Feed, alle Felder konsistent
- media_url, Caption, Hashtags, Category, Location, Poster geprüft
- Demo-Seed wird korrekt verdrängt

### API-Konsistenz
- Einheitliches success/data/error-Muster für Feed, Like, View, Comments, Single Post

### Verbleibende Restpunkte
- Replies für Kommentare
- Bookmark/Save
- Following/"Für dich"
- Ranking/Recommendation
- Animationen/Mikrointeraktionen

### Performance & Cleanup
- Videos werden lazy geladen, preload sparsam
- Pause/Play und Event-Listener werden sauber aufgeräumt
- Keine Memory-Leaks, keine parallelen Player

### Testfälle & Edge-Cases
- Feed mit echter DB und echten Posts
- Feed mit leerer DB
- Feed mit Demo-Fallback
- Kaputte media_url, fehlendes Poster, ungültige API-Antwort, API 500, Netzwerkfehler
- Mehrere Videos im Scrollbetrieb
- Mobile und Desktop getestet

### Verbleibende Restpunkte
- Echte Like-/View-DB-Logik
- Kommentar-/Save-API
- Recommendation/Ranking
- User-spezifische Feeds

## Frontend-Status (TikTok-Feed)

- Feed-UI ist jetzt ein vertikaler, mobiler, TikTok-Style Video-Feed
- Snap-Scroll, Video-Autoplay, Action-Bar, Info-Overlay, Cyberpunk-Look
- State-Handling: Fehler, Empty-State, Feed-Items
- Responsive: Mobile = Vollbild, Desktop = mittig, atmosphärisch
- Videos werden automatisch abgespielt/pausiert, Sound togglebar
- Demo-Seed greift, wenn keine echten Daten
- Keine Breaking Changes für spätere echte Daten
- Siehe feed.js und feed.css für Details
