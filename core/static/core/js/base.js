// Notification badge
(function() {
  const badge = document.getElementById('unread-badge');
  if (!badge) return;

  const scriptTag = document.currentScript;
  const unreadUrl = scriptTag.dataset.unreadUrl;

  function fetchUnreadCount() {
    fetch(unreadUrl)
      .then(response => response.json())
      .then(data => {
        if (data.count > 0) {
          badge.textContent = data.count;
          badge.style.display = 'inline';
        } else {
          badge.style.display = 'none';
        }
      })
      .catch(() => {});
  }

  fetchUnreadCount();
  setInterval(fetchUnreadCount, 5000);
})();

// Toast initialization
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.toast').forEach(el => {
    new bootstrap.Toast(el).show();
  });
});