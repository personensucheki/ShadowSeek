# ShadowSeek Live-Modul – Entwicklerhinweise

## JavaScript-Entwicklung

- Für alle Fragen zu Vanilla-JS, DOM, Events, Fetch, Promises, async/await etc. gilt:
  - **MDN Web Docs:** https://developer.mozilla.org/de/
  - **ECMAScript-Referenz:** https://262.ecma-international.org/
- Beispiel: Wie funktioniert `fetch`?
  - https://developer.mozilla.org/de/docs/Web/API/Fetch_API/Using_Fetch
- Beispiel: Wie funktioniert `addEventListener`?
  - https://developer.mozilla.org/de/docs/Web/API/EventTarget/addEventListener

## Live-API
- Alle Endpunkte liefern und erwarten JSON.
- Siehe `app/routes/live_api_v2.py` für Details.

## Style Guide
- UI-Elemente im Live-Bereich folgen Cyberpunk-Design:
  - Neon-Pink: #FF00FF
  - Neon-Grün: #00FF9F
  - Schwarzer Hintergrund
- Bestehende CSS-Klassen verwenden und erweitern, keine Inline-Styles.

## Hinweise
- Bei Fragen zu modernen JS-Patterns, bitte immer zuerst MDN/ECMAScript konsultieren.
- Für Python/Flask: Siehe offizielle Flask- und SQLAlchemy-Doku.
