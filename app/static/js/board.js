/**
 * board.js — Kanban drag & drop using SortableJS + HTMX
 */

// Get app base path from meta tag
const APP_BASE_PATH = document.querySelector('meta[name="app-base-path"]')?.content || '';

function buildUrl(path) {
  const basePath = APP_BASE_PATH.replace(/\/$/, '');
  const cleanPath = '/' + path.replace(/^\//, '');
  return basePath ? `${basePath}${cleanPath}` : cleanPath;
}

document.addEventListener('DOMContentLoaded', () => {
  initBoard();
});

function initBoard() {
  const columns = document.querySelectorAll('.sortable-column');
  if (!columns.length) return;

  columns.forEach(col => {
    Sortable.create(col, {
      group: 'kanban',           // same group = cards can move between columns
      animation: 150,
      ghostClass: 'sortable-ghost',
      dragClass: 'sortable-drag',
      handle: '.ticket-card',
      draggable: '.ticket-card',

      onStart() {
        // Highlight all drop zones
        document.querySelectorAll('.sortable-column').forEach(c => {
          c.classList.add('drag-over');
        });
      },

      onEnd(evt) {
        document.querySelectorAll('.sortable-column').forEach(c => {
          c.classList.remove('drag-over');
        });

        const card = evt.item;
        const newCol = evt.to;
        const ticketId = card.dataset.ticketId;
        const newStatusId = newCol.dataset.statusId;
        const oldStatusId = card.dataset.statusId;

        if (!ticketId || newStatusId === oldStatusId) return;

        // Send status update to server
        const formData = new FormData();
        formData.append('status_id', newStatusId);

        fetch(buildUrl(`/tickets/${ticketId}/status`), {
          method: 'POST',
          body: formData,
        })
          .then(res => {
            if (!res.ok) {
              // Revert DOM move
              const origCol = document.getElementById('col-' + oldStatusId);
              if (origCol) origCol.appendChild(card);
              showToast('No tienes permiso para mover este ticket.', 'danger');
              return;
            }
            return res.text();
          })
          .then(html => {
            if (!html) return;
            // Replace card with updated HTML from server
            const temp = document.createElement('div');
            temp.innerHTML = html;
            const newCard = temp.firstElementChild;
            if (newCard) {
              card.replaceWith(newCard);
            }
            updateColumnCounts();
          })
          .catch(() => {
            showToast('Error al actualizar el ticket.', 'danger');
          });
      },
    });
  });
}

/** Recalculate column header counts */
function updateColumnCounts() {
  document.querySelectorAll('.board-col').forEach(col => {
    const count = col.querySelectorAll('.ticket-card').length;
    const badge = col.querySelector('.board-col-count');
    if (badge) badge.textContent = count;
  });
}

/** Show a Bootstrap toast notification */
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const id = 'toast-' + Date.now();
  const html = `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert">
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto"
                data-bs-dismiss="toast"></button>
      </div>
    </div>`;
  container.insertAdjacentHTML('beforeend', html);
  const toastEl = document.getElementById(id);
  new bootstrap.Toast(toastEl, { delay: 4000 }).show();
  toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// Expose for inline use
window.showToast = showToast;
