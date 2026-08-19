document.addEventListener('DOMContentLoaded', () => {
  const modalElement = document.getElementById('clienteModal');
  const form = document.getElementById('clientForm');
  if (!modalElement || !form) return;

  const modal = new bootstrap.Modal(modalElement);
  let isEditMode = false;
  let selectedClient = null;
  const title = document.getElementById('clientModalTitle');
  const errors = document.getElementById('clientFormErrors');
  const saveButton = document.getElementById('clientSave');
  const fields = ['nombre', 'telefono', 'correo', 'direccion', 'cedula_ruc'];

  document.querySelectorAll('.js-edit-client').forEach((button) => {
    button.addEventListener('click', () => {
      selectedClient = {
        id: button.dataset.id,
        url: button.dataset.url,
      };
      isEditMode = true;
      title.textContent = 'Editar Cliente';
      fields.forEach((field) => {
        form.elements[field].value = button.getAttribute(`data-${field.replace('_', '-')}`) || '';
      });
      hideErrors();
      modal.show();
    });
  });

  modalElement.addEventListener('show.bs.modal', () => {
    if (isEditMode) return;
    title.textContent = 'Nuevo Cliente';
    form.reset();
    hideErrors();
  });

  modalElement.addEventListener('hidden.bs.modal', () => {
    isEditMode = false;
    selectedClient = null;
    form.reset();
    hideErrors();
  });

  form.addEventListener('submit', async (event) => {
    if (!isEditMode) return;
    event.preventDefault();
    if (!selectedClient || !form.reportValidity()) return;

    saveButton.disabled = true;
    saveButton.textContent = 'Guardando';
    hideErrors();
    try {
      const response = await fetch(selectedClient.url, {
        method: 'PATCH',
        headers: {
          'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value,
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        },
        body: new URLSearchParams(new FormData(form)),
        credentials: 'same-origin',
      });
      const payload = await response.json();
      if (!response.ok) throw payload;
      updateClientRow(payload);
      modal.hide();
    } catch (payload) {
      const fallback = { general: [{ message: 'No se pudo actualizar el cliente.' }] };
      const messages = Object.values(payload.errors || fallback)
        .flat()
        .map((item) => item.message)
        .join(' ');
      errors.textContent = messages;
      errors.classList.remove('d-none');
    } finally {
      saveButton.disabled = false;
      saveButton.textContent = 'Guardar';
    }
  });

  function updateClientRow(client) {
    const row = document.querySelector(`[data-client-id="${client.id}"]`);
    if (!row) return;
    fields.forEach((field) => {
      const cell = row.querySelector(`[data-field="${field}"]`);
      if (cell) cell.textContent = client[field] || '';
    });
    const button = row.querySelector('.js-edit-client');
    if (button) {
      fields.forEach((field) => {
        button.setAttribute(`data-${field.replace('_', '-')}`, client[field] || '');
      });
    }
  }

  function hideErrors() {
    errors.textContent = '';
    errors.classList.add('d-none');
  }
});
