let nextCursor = null;
let loading = false;

function createCard(item) {
  const card = document.createElement("article");
  card.className = "feed-card";

  const mediaWrap = document.createElement("div");
  mediaWrap.className = "feed-media";

  let mediaEl;
  if (item.media_type === "photo") {
    mediaEl = document.createElement("img");
    mediaEl.loading = "lazy";
    mediaEl.alt = item.caption || "Foto";
    mediaEl.src = item.media_url;
  } else {
    mediaEl = document.createElement("video");
    mediaEl.src = item.media_url;
    mediaEl.playsInline = true;
    mediaEl.controls = true;
    mediaEl.preload = "metadata";
  }
  mediaWrap.appendChild(mediaEl);

  const overlay = document.createElement("div");
  overlay.className = "feed-overlay";

  const userRow = document.createElement("div");
  userRow.className = "feed-user";

  const avatar = document.createElement("img");
  avatar.className = "feed-avatar";
  avatar.src = item.avatar_url;
  avatar.alt = item.username;

  const userLink = document.createElement("a");
  userLink.href = item.profile_url || "#";
  userLink.textContent = item.display_name || item.username;

  userRow.appendChild(avatar);
  userRow.appendChild(userLink);

  const caption = document.createElement("div");
  caption.className = "feed-caption";
  caption.textContent = item.caption || "";

  const stats = document.createElement("div");
  stats.className = "feed-stats";
  stats.textContent = `♥ ${item.like_count || 0} · ▶ ${item.view_count || 0}`;

  overlay.appendChild(userRow);
  if (item.caption) overlay.appendChild(caption);
  overlay.appendChild(stats);

  mediaWrap.appendChild(overlay);
  card.appendChild(mediaWrap);
  return card;
}

async function loadMore() {
  if (loading) return;
  loading = true;
  const stage = document.getElementById("feed-stage");
  const loadingEl = document.getElementById("feed-loading");
  if (loadingEl) loadingEl.textContent = "Feed wird geladen…";

  const params = new URLSearchParams();
  params.set("limit", "10");
  if (nextCursor) params.set("cursor", nextCursor);

  try {
    const res = await fetch(`/api/feed?${params.toString()}`, { credentials: "same-origin" });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.error || "Feed error");

    if (loadingEl) loadingEl.remove();
    (data.items || []).forEach((item) => stage.appendChild(createCard(item)));
    nextCursor = data.next_cursor || null;

    if (!nextCursor && (data.items || []).length === 0) {
      const empty = document.createElement("div");
      empty.className = "feed-loading";
      empty.textContent = "Noch keine Uploads. Lade ein Video oder Foto hoch.";
      stage.appendChild(empty);
    }
  } catch (e) {
    if (loadingEl) loadingEl.textContent = "Feed konnte nicht geladen werden.";
  } finally {
    loading = false;
  }
}

function onScroll() {
  if (!nextCursor && document.querySelectorAll(".feed-card").length > 0) return;
  const nearBottom = window.innerHeight + window.scrollY > document.body.offsetHeight - 1200;
  if (nearBottom) loadMore();
}

document.addEventListener("DOMContentLoaded", () => {
  loadMore();
  window.addEventListener("scroll", onScroll, { passive: true });
});

