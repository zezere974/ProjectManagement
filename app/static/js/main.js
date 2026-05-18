// Utilitaires JavaScript — Daily Management App
// Gestion du timer standup, des toasts, du thème et des interactions UI

'use strict';

// ===== Configuration =====
const APP_CONFIG = {
  standupDuration: 15 * 60, // 15 minutes en secondes
  toastDuration: 4000,       // Durée d'affichage des toasts (ms)
};

// ===== Timer Standup (Alpine.js) =====
// Exposé via Alpine.js dans standup.html
function standupTimer(durationSeconds = APP_CONFIG.standupDuration) {
  return {
    totalSeconds: durationSeconds,
    remaining: durationSeconds,
    running: false,
    finished: false,
    _interval: null,

    get minutes() {
      return Math.floor(this.remaining / 60);
    },

    get seconds() {
      return this.remaining % 60;
    },

    get formattedTime() {
      const m = String(this.minutes).padStart(2, '0');
      const s = String(this.seconds).padStart(2, '0');
      return `${m}:${s}`;
    },

    get progressPct() {
      return ((this.totalSeconds - this.remaining) / this.totalSeconds) * 100;
    },

    get timerColor() {
      const pct = this.progressPct;
      if (pct >= 90) return '#ef4444'; // Rouge — temps presque écoulé
      if (pct >= 70) return '#eab308'; // Jaune — attention
      return '#22c55e';               // Vert — dans les temps
    },

    start() {
      if (this.running || this.finished) return;
      this.running = true;
      this._interval = setInterval(() => {
        if (this.remaining > 0) {
          this.remaining--;
        } else {
          this.stop();
          this.finished = true;
          this.onFinish();
        }
      }, 1000);
    },

    pause() {
      this.running = false;
      clearInterval(this._interval);
    },

    reset() {
      this.pause();
      this.remaining = this.totalSeconds;
      this.finished = false;
    },

    stop() {
      this.running = false;
      clearInterval(this._interval);
    },

    onFinish() {
      // Notification sonore et visuelle en fin de timer
      showToast('⏰ Temps écoulé ! Le standup est terminé.', 'warning');
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Standup terminé', {
          body: 'Le temps de 15 minutes est écoulé.',
          icon: '/static/img/icon.png',
        });
      }
    },

    requestNotificationPermission() {
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
      }
    },
  };
}

// ===== Gestion des Toasts =====
let toastContainer = null;

function getToastContainer() {
  if (!toastContainer) {
    toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toast-container';
      toastContainer.style.cssText = `
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        pointer-events: none;
      `;
      document.body.appendChild(toastContainer);
    }
  }
  return toastContainer;
}

function showToast(message, type = 'info', duration = APP_CONFIG.toastDuration) {
  const container = getToastContainer();

  const colors = {
    success: { bg: 'rgba(34, 197, 94, 0.1)', border: 'rgba(34, 197, 94, 0.3)', text: '#22c55e', icon: '✓' },
    error:   { bg: 'rgba(239, 68, 68, 0.1)',  border: 'rgba(239, 68, 68, 0.3)',  text: '#ef4444', icon: '✕' },
    warning: { bg: 'rgba(234, 179, 8, 0.1)',  border: 'rgba(234, 179, 8, 0.3)',  text: '#eab308', icon: '⚠' },
    info:    { bg: 'rgba(59, 130, 246, 0.1)', border: 'rgba(59, 130, 246, 0.3)', text: '#60a5fa', icon: 'ℹ' },
  };

  const style = colors[type] || colors.info;

  const toast = document.createElement('div');
  toast.style.cssText = `
    background: ${style.bg};
    border: 1px solid ${style.border};
    color: ${style.text};
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    pointer-events: auto;
    cursor: pointer;
    animation: fadeIn 0.3s ease forwards;
    backdrop-filter: blur(8px);
    max-width: 380px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  `;
  toast.innerHTML = `<span>${style.icon}</span><span>${message}</span>`;
  toast.addEventListener('click', () => toast.remove());

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ===== Gestion Sidebar Mobile =====
function initSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const toggleBtn = document.getElementById('sidebar-toggle');

  if (!sidebar) return;

  toggleBtn?.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay?.classList.toggle('hidden');
  });

  overlay?.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.add('hidden');
  });
}

// ===== Progress Bar Color =====
function updateProgressColors() {
  document.querySelectorAll('[data-progress]').forEach(el => {
    const pct = parseInt(el.dataset.progress, 10);
    const fill = el.querySelector('.progress-bar-fill');
    if (!fill) return;

    if (pct >= 100) fill.style.backgroundColor = '#22c55e';
    else if (pct >= 80) fill.style.backgroundColor = '#3b82f6';
    else if (pct >= 50) fill.style.backgroundColor = '#eab308';
    else fill.style.backgroundColor = '#ef4444';

    fill.style.width = `${pct}%`;
  });
}

// ===== Confirmation de suppression =====
function confirmDelete(message = 'Confirmer la suppression ?') {
  return window.confirm(message);
}

// ===== HTMX helpers =====
// Événement déclenché après chaque requête HTMX réussie
document.addEventListener('htmx:afterRequest', function (event) {
  if (event.detail.xhr.status >= 200 && event.detail.xhr.status < 300) {
    updateProgressColors();
  }
});

// Gestion des erreurs HTMX
document.addEventListener('htmx:responseError', function (event) {
  const status = event.detail.xhr.status;
  if (status === 401) {
    showToast('Session expirée. Veuillez vous reconnecter.', 'error');
    setTimeout(() => { window.location.href = '/login'; }, 2000);
  } else if (status === 403) {
    showToast('Accès non autorisé.', 'error');
  } else {
    showToast(`Erreur ${status} — veuillez réessayer.`, 'error');
  }
});

// ===== Initialisation =====
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  updateProgressColors();

  // Auto-dismiss des flash messages
  setTimeout(() => {
    document.querySelectorAll('.flash-message').forEach(el => {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.5s ease';
      setTimeout(() => el.remove(), 500);
    });
  }, 5000);

  // Activer le lien de navigation courant
  const currentPath = window.location.pathname;
  document.querySelectorAll('.sidebar-nav-item').forEach(link => {
    const href = link.getAttribute('href');
    if (href && (currentPath === href || (href !== '/' && currentPath.startsWith(href)))) {
      link.classList.add('active');
    }
  });
});

// ===== Utilitaires export =====
window.DailyMgmt = {
  showToast,
  confirmDelete,
  standupTimer,
};
