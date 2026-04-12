async function loadProfilePosts(username) {
  const grid = document.getElementById("pp-grid");
  if (!grid) return;
  grid.textContent = "Lade…";
  try {
    const res = await fetch(`/api/u/${encodeURIComponent(username)}/posts?limit=48`, {
      credentials: "same-origin",
    });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.error || "Load failed");

    grid.textContent = "";
    const items = data.items || [];
    if (!items.length) {
      grid.textContent = "Noch keine Uploads.";
      return;
    }

    items.forEach((post) => {
      const tile = document.createElement("a");
      tile.className = "pp-tile";
      tile.href = post.media_url;
      tile.target = "_blank";
      tile.rel = "noreferrer";

      let mediaEl;
      if (post.media_type === "photo") {
        mediaEl = document.createElement("img");
        mediaEl.loading = "lazy";
        mediaEl.src = post.media_url;
        mediaEl.alt = post.caption || "Foto";
      } else {
        mediaEl = document.createElement("video");
        mediaEl.src = post.media_url;
        mediaEl.muted = true;
        mediaEl.playsInline = true;
        mediaEl.preload = "metadata";
      }
      tile.appendChild(mediaEl);

      const meta = document.createElement("div");
      meta.className = "pp-tile-meta";
      meta.textContent = `▶ ${post.view_count || 0}`;
      tile.appendChild(meta);

      grid.appendChild(tile);
    });
  } catch (e) {
    grid.textContent = "Posts konnten nicht geladen werden.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const username = window.SHADOWSEEK_PROFILE_USERNAME;
  if (username) loadProfilePosts(username);

  const share = document.getElementById("pp-share");
  if (share) {
    share.addEventListener("click", async () => {
      const url = window.location.href;
      try {
        if (navigator.share) {
          await navigator.share({ title: "ShadowSeek Profil", url });
        } else {
          await navigator.clipboard.writeText(url);
          share.title = "Link kopiert";
        }
      } catch {
        // ignore
      }
    });
  }

  const settings = document.getElementById("pp-settings");
  if (settings) {
    settings.addEventListener("click", () => {
      alert("Einstellungen kommen als Nächstes (MVP).");
    });
  }
});

