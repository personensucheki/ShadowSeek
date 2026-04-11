document.addEventListener('DOMContentLoaded', function() {
	const widget = document.getElementById('chatbot-widget');
	const minimizeBtn = document.getElementById('chatbot-minimize');
	const closeBtn = document.getElementById('chatbot-close');
	let minimized = false;

	// Öffnen durch Klick auf FAB (Sprechblase)
	let fab = document.getElementById('chat-toggle');
	if (fab) {
		fab.addEventListener('click', function() {
			widget.classList.remove('minimized');
			widget.style.display = 'flex';
		});
	}

	// Minimieren
	if (minimizeBtn) {
		minimizeBtn.addEventListener('click', function() {
			widget.classList.toggle('minimized');
			minimized = !minimized;
		});
	}

	// Schließen
	if (closeBtn) {
		closeBtn.addEventListener('click', function() {
			widget.style.display = 'none';
		});
	}

	// Mobil: Widget anpassen
	function handleResize() {
		if (window.innerWidth < 600) {
			widget.style.width = '98vw';
			widget.style.right = '1vw';
			widget.style.bottom = '1vw';
		} else {
			widget.style.width = '340px';
			widget.style.right = '30px';
			widget.style.bottom = '30px';
		}
	}
	window.addEventListener('resize', handleResize);
	handleResize();
});
