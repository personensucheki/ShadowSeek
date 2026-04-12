// Kommentar-Modal
function openCommentsModal(item) {
  let modal = document.getElementById("comments-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "comments-modal";
    modal.className = "comments-modal";
    document.body.appendChild(modal);
  }
  modal.innerHTML = `<div class="comments-backdrop"></div><div class="comments-content"><div class="comments-header">Kommentare<button class="comments-close">×</button></div><div class="comments-list"></div><form class="comments-form"><input type="text" name="content" maxlength="500" placeholder="Kommentar schreiben..." autocomplete="off" required><button type="submit">Senden</button></form></div>`;
  modal.style.display = "flex";
  modal.querySelector(".comments-close").onclick = () => { modal.style.display = "none"; };
  modal.querySelector(".comments-backdrop").onclick = () => { modal.style.display = "none"; };
  // Laden
  const list = modal.querySelector(".comments-list");
  list.innerHTML = "<div class='comments-loading'>Lade Kommentare…</div>";
  fetch(`/api/feed/${item.id}/comments`).then(r=>r.json()).then(data => {
    if (!data.success) {
      list.innerHTML = `<div class='comments-error'>Fehler beim Laden.</div>`;
      return;
    }
    if (!data.items.length) {
      list.innerHTML = `<div class='comments-empty'>Noch keine Kommentare.</div>`;
      return;
    }
    list.innerHTML = "";
    data.items.forEach(c => {
      const el = document.createElement("div");
      el.className = "comment-item";
      el.innerHTML = `<span class='comment-user'>${c.display_name || c.username}</span><span class='comment-content'>${c.content}</span><span class='comment-date'>${new Date(c.created_at).toLocaleString()}</span>`;
      list.appendChild(el);
    });
  });
  // Absenden
  const form = modal.querySelector(".comments-form");
  form.onsubmit = async (e) => {
    e.preventDefault();
    const content = form.content.value.trim();
    if (!content) return;
    form.querySelector("button").disabled = true;
    try {
      const res = await fetch(`/api/feed/${item.id}/comments`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({content})});
      const data = await res.json();
      if (data.success && data.comment) {
        const el = document.createElement("div");
        el.className = "comment-item";
        el.innerHTML = `<span class='comment-user'>${data.comment.display_name || data.comment.username}</span><span class='comment-content'>${data.comment.content}</span><span class='comment-date'>${new Date(data.comment.created_at).toLocaleString()}</span>`;
        list.appendChild(el);
        form.reset();
      } else if (data.error && data.error.code === "not_authenticated") {
        alert("Bitte einloggen, um zu kommentieren.");
      } else if (data.error) {
        alert(data.error.message);
      }
    } catch (err) {
      alert("Kommentar konnte nicht gespeichert werden.");
    } finally {
      form.querySelector("button").disabled = false;
    }
  };
}
let nextCursor = null;

let nextCursor = null;
let loading = false;
let feedItems = [];

function createFeedItem(item, idx) {
  const card = document.createElement("section");
  card.className = "feed-card snap-section";

  // Media
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
    mediaEl.muted = true;
    mediaEl.preload = "metadata";
    mediaEl.setAttribute("webkit-playsinline", "true");
    mediaEl.setAttribute("playsinline", "true");
    mediaEl.setAttribute("tabindex", "0");
    mediaEl.poster = item.poster_url || "/static/images/default-poster.jpg";
    mediaEl.className = "feed-video";
    // Mute toggle
    const muteBtn = document.createElement("button");
    muteBtn.className = "mute-btn";
    muteBtn.title = "Ton an/aus";
    muteBtn.innerHTML = '<svg width="28" height="28" viewBox="0 0 28 28"><path d="M4 10v8h6l6 6V4l-6 6H4z" fill="#fff"/></svg>';
    muteBtn.onclick = (e) => {
      e.stopPropagation();
      mediaEl.muted = !mediaEl.muted;
      muteBtn.classList.toggle("active", !mediaEl.muted);
    };
    mediaWrap.appendChild(muteBtn);
    mediaEl.onclick = () => {
      mediaEl.muted = !mediaEl.muted;
      muteBtn.classList.toggle("active", !mediaEl.muted);
    };
  }
  mediaWrap.appendChild(mediaEl);

  // Action Bar
  const actionBar = document.createElement("div");
  actionBar.className = "feed-action-bar";

  // Like-Button
  const likeBtn = document.createElement("div");
  likeBtn.className = "action likes";
  likeBtn.title = "Like";
  let liked = !!item.liked;
  let likeCount = item.like_count ?? 0;
  likeBtn.innerHTML = `❤️<span>${likeCount}</span>`;
  if (liked) likeBtn.classList.add("liked");
  likeBtn.onclick = async (e) => {
    e.stopPropagation();
    likeBtn.disabled = true;
    try {
      const res = await fetch(`/api/feed/${item.id}/like`, {method: "POST", headers: {"Content-Type": "application/json"}});
      const data = await res.json();
      if (data.success) {
        liked = data.liked;
        likeCount = data.like_count;
        likeBtn.querySelector("span").textContent = likeCount;
        likeBtn.classList.toggle("liked", liked);
      } else if (data.error && data.error.code === "not_authenticated") {
        alert("Bitte einloggen, um zu liken.");
      }
    } catch (err) {
      alert("Like fehlgeschlagen.");
    } finally {
      likeBtn.disabled = false;
    }
  };

  // Kommentar-Button
  const commentBtn = document.createElement("div");
  commentBtn.className = "action comments";
  commentBtn.title = "Kommentare";
  commentBtn.innerHTML = `💬<span>${item.comment_count ?? 0}</span>`;
  commentBtn.onclick = (e) => {
    e.stopPropagation();
    openCommentsModal(item);
  };

  // Views
  const viewBtn = document.createElement("div");
  viewBtn.className = "action views";
  viewBtn.title = "Views";
  viewBtn.innerHTML = `▶<span>${item.views ?? item.view_count ?? 0}</span>`;

  // Share
  const shareBtn = document.createElement("div");
  shareBtn.className = "action share";
  shareBtn.title = "Teilen";
  shareBtn.innerHTML = `🔗`;
  shareBtn.onclick = (e) => {
    e.stopPropagation();
    const url = `${window.location.origin}/feed/post/${item.id}`;
    navigator.clipboard.writeText(url);
    shareBtn.classList.add("shared");
    setTimeout(()=>shareBtn.classList.remove("shared"), 1200);
  };

  actionBar.appendChild(likeBtn);
  actionBar.appendChild(viewBtn);
  actionBar.appendChild(commentBtn);
  actionBar.appendChild(shareBtn);
  mediaWrap.appendChild(actionBar);

  // Overlay
  const overlay = document.createElement("div");
  overlay.className = "feed-overlay";

  const userRow = document.createElement("div");
  userRow.className = "feed-user";

  const avatar = document.createElement("img");
  avatar.className = "feed-avatar";
  avatar.src = item.avatar_url;
  avatar.alt = item.username;
  avatar.style.cursor = "pointer";
  avatar.onclick = (e) => {
    e.stopPropagation();
    if (item.profile_url) window.location.href = item.profile_url;
  };
  const userLink = document.createElement("a");
  userLink.href = item.profile_url || "#";
  userLink.textContent = item.display_name || item.username;
  userLink.onclick = (e) => {
    if (!item.profile_url) e.preventDefault();
  };
  userRow.appendChild(avatar);
  userRow.appendChild(userLink);

  const caption = document.createElement("div");
  caption.className = "feed-caption";
  caption.textContent = item.caption || "";

  const hashtags = document.createElement("div");
  hashtags.className = "feed-hashtags";
  hashtags.textContent = item.hashtags || "";

  const meta = document.createElement("div");
  meta.className = "feed-meta";
  meta.textContent = [item.category, item.location].filter(Boolean).join(" · ");

  overlay.appendChild(userRow);
  if (item.caption) overlay.appendChild(caption);
  if (item.hashtags) overlay.appendChild(hashtags);
  if (item.category || item.location) overlay.appendChild(meta);

  mediaWrap.appendChild(overlay);
  card.appendChild(mediaWrap);
  return card;
}

function renderFeed(items) {
  const stage = document.getElementById("feed-stage");
  stage.innerHTML = "";
  if (!items || items.length === 0) {
    const empty = document.createElement("div");
    empty.className = "feed-empty-state";
    empty.innerHTML = `
      <div class="empty-illustration"></div>
      <div class="empty-text">Noch keine Uploads.</div>
      <a href="/upload" class="feed-cta">Zum Upload</a>
      <button class="feed-cta-alt" onclick="window.location.reload()">Testfeed laden</button>
    `;
    stage.appendChild(empty);
    return;
  }
  items.forEach((item, idx) => {
    stage.appendChild(createFeedItem(item, idx));
  });
  setupSnapScroll();
  setupVideoAutoplay();
}

async function loadFeed() {
  loading = true;
  const stage = document.getElementById("feed-stage");
  const loadingEl = document.getElementById("feed-loading");
  if (loadingEl) loadingEl.textContent = "Feed wird geladen…";
  try {
    const res = await fetch(`/api/feed?limit=10`, { credentials: "same-origin" });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.error?.message || "Feed error");
    feedItems = data.items || [];
    if (loadingEl) loadingEl.remove();
    renderFeed(feedItems);
  } catch (e) {
    if (loadingEl) loadingEl.textContent = "Feed konnte nicht geladen werden.";
    const stage = document.getElementById("feed-stage");
    stage.innerHTML = `<div class="feed-error"><div>Feed konnte nicht geladen werden.</div><button onclick="window.location.reload()">Erneut versuchen</button></div>`;
  } finally {
    loading = false;
  }
}

function setupSnapScroll() {
  const stage = document.getElementById("feed-stage");
  stage.style.scrollSnapType = "y mandatory";
  Array.from(stage.children).forEach((el) => {
    el.classList.add("snap-section");
    el.style.scrollSnapAlign = "start";
  });
}


function setupVideoAutoplay() {
  const videos = Array.from(document.querySelectorAll("video.feed-video"));
  if (!('IntersectionObserver' in window)) return;
  let currentPlaying = null;
  let viewTimeouts = new Map();
  let viewedPosts = new Set();
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const video = entry.target;
      const idx = Array.from(videos).indexOf(video);
      const item = feedItems[idx];
      if (!item) return;
      if (entry.isIntersecting && entry.intersectionRatio > 0.6) {
        if (currentPlaying && currentPlaying !== video) {
          currentPlaying.pause();
        }
        video.play().catch(()=>{});
        currentPlaying = video;
        // View-Tracking mit debounce
        if (!viewedPosts.has(item.id)) {
          if (viewTimeouts.has(video)) clearTimeout(viewTimeouts.get(video));
          viewTimeouts.set(video, setTimeout(() => {
            fetch(`/api/feed/${item.id}/view`, {method: "POST", headers: {"Content-Type": "application/json"}});
            viewedPosts.add(item.id);
          }, 1200)); // 1.2s sichtbar
        }
      } else {
        video.pause();
        if (viewTimeouts.has(video)) {
          clearTimeout(viewTimeouts.get(video));
          viewTimeouts.delete(video);
        }
      }
    });
  }, { threshold: [0.6] });
  videos.forEach(video => observer.observe(video));
  // Cleanup bei Navigation
  window.addEventListener("beforeunload", () => {
    observer.disconnect();
    viewTimeouts.forEach(timeout => clearTimeout(timeout));
    viewTimeouts.clear();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadFeed();
});

