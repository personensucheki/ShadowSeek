document.addEventListener('DOMContentLoaded', function() {
  const cards = document.getElementById('date-match-cards');
  const empty = document.getElementById('date-match-empty');
  const errorBox = document.getElementById('date-match-error');
  const matchesBox = document.getElementById('date-match-matches');

  function showError(msg) {
    errorBox.style.display = 'block';
    errorBox.textContent = msg;
  }
  function hideError() {
    errorBox.style.display = 'none';
    errorBox.textContent = '';
  }

  function fetchCandidates() {
    fetch('/api/date-match/discover').then(r => r.json()).then(res => {
      if (!res.success) return showError(res.error || 'Fehler beim Laden');
      if (!res.data.length) {
        cards.innerHTML = '';
        empty.style.display = 'block';
        return;
      }
      empty.style.display = 'none';
      cards.innerHTML = '';
      res.data.forEach(u => {
        const card = document.createElement('div');
        card.className = 'date-match-card';
        card.innerHTML = `
          <img src="${u.avatar_url || '/static/img/default_avatar.png'}" class="date-match-avatar">
          <div class="date-match-info">
            <strong>${u.username}</strong><br>
            ${u.real_name || ''}<br>
            ${u.age ? 'Alter: ' + u.age : ''}
          </div>
          <div class="date-match-actions">
            <button data-action="left" data-id="${u.id}" class="swipe-btn left">👎</button>
            <button data-action="right" data-id="${u.id}" class="swipe-btn right">👍</button>
            <button data-action="super" data-id="${u.id}" class="swipe-btn super">💚</button>
          </div>
        `;
        cards.appendChild(card);
      });
    }).catch(() => showError('Netzwerkfehler'));
  }

  cards.addEventListener('click', function(e) {
    if (e.target.classList.contains('swipe-btn')) {
      const id = parseInt(e.target.getAttribute('data-id'));
      const action = e.target.getAttribute('data-action');
      hideError();
      fetch('/api/date-match/swipe', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({target_user_id: id, action})
      }).then(r => r.json()).then(res => {
        if (!res.success) return showError(res.error || 'Fehler beim Swipen');
        fetchCandidates();
        if (res.data && res.data.match) {
          alert('It\'s a match!');
          fetchMatches();
        }
      }).catch(() => showError('Netzwerkfehler'));
    }
  });

  function fetchMatches() {
    fetch('/api/date-match/list').then(r => r.json()).then(res => {
      if (!res.success) return showError(res.error || 'Fehler beim Laden der Matches');
      matchesBox.innerHTML = '';
      if (!res.data.length) {
        matchesBox.innerHTML = '<em>Keine Matches.</em>';
        return;
      }
      res.data.forEach(m => {
        const div = document.createElement('div');
        div.className = 'date-match-match';
        div.innerHTML = `
          <img src="${m.avatar_url || '/static/img/default_avatar.png'}" class="date-match-avatar">
          <strong>${m.username}</strong> (${m.real_name || ''})
          <button class="unmatch-btn" data-id="${m.id}">Unmatch</button>
        `;
        matchesBox.appendChild(div);
      });
    });
  }

  matchesBox.addEventListener('click', function(e) {
    if (e.target.classList.contains('unmatch-btn')) {
      const id = parseInt(e.target.getAttribute('data-id'));
      hideError();
      fetch('/api/date-match/unmatch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({target_user_id: id})
      }).then(r => r.json()).then(res => {
        if (!res.success) return showError(res.error || 'Fehler beim Unmatchen');
        fetchMatches();
      });
    }
  });

  fetchCandidates();
  fetchMatches();
});
