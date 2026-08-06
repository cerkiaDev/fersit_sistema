/* Un solo modal para crear y editar productos sin salir del catálogo. */
document.addEventListener('DOMContentLoaded', () => {
  const modalElement = document.getElementById('prodModal');
  const form = document.getElementById('productForm');
  if (!modalElement || !form) return;

  const modal = new bootstrap.Modal(modalElement);
  let isEditModalOpen = false;
  let selectedProduct = null;
  const title = document.getElementById('productModalTitle');
  const name = document.getElementById('productName');
  const description = document.getElementById('productDescription');
  const price = document.getElementById('productPrice');
  const image = document.getElementById('productImage');
  const imageStatus = document.getElementById('productImageStatus');
  const active = document.getElementById('productoActivo');
  const errors = document.getElementById('productFormErrors');
  const saveButton = document.getElementById('productSave');

  document.querySelectorAll('.js-edit-product').forEach((button) => {
    button.addEventListener('click', () => {
      selectedProduct = {
        id: button.dataset.id,
        url: button.dataset.url,
        nombre: button.dataset.nombre,
        descripcion: button.dataset.descripcion,
        precio: button.dataset.precio,
        activo: button.dataset.activo === 'true',
        imagen: button.dataset.imagen || '',
      };
      isEditModalOpen = true;
      title.textContent = 'Editar Producto';
      name.value = selectedProduct.nombre;
      description.value = selectedProduct.descripcion;
      price.value = selectedProduct.precio;
      active.checked = selectedProduct.activo;
      image.value = '';
      imageStatus.textContent = selectedProduct.imagen ? 'Imagen actual disponible. Selecciona un archivo para reemplazarla.' : 'Sin archivos seleccionados';
      hideErrors();
      modal.show();
    });
  });

  image.addEventListener('change', () => {
    imageStatus.textContent = image.files[0]?.name || 'Sin archivos seleccionados';
  });

  modalElement.addEventListener('show.bs.modal', () => {
    if (isEditModalOpen) return;
    title.textContent = 'Nuevo Producto';
    form.reset();
    active.checked = true;
    imageStatus.textContent = 'Sin archivos seleccionados';
    hideErrors();
  });

  modalElement.addEventListener('hidden.bs.modal', () => {
    isEditModalOpen = false;
    selectedProduct = null;
    form.reset();
    hideErrors();
  });

  form.addEventListener('submit', async (event) => {
    if (!isEditModalOpen) return;
    event.preventDefault();
    if (!selectedProduct || !form.reportValidity()) return;

    saveButton.disabled = true;
    saveButton.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span> Guardando';
    hideErrors();
    try {
      const response = await fetch(selectedProduct.url, {
        method: 'PATCH',
        headers: {
          'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value,
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: new FormData(form),
        credentials: 'same-origin',
      });
      const payload = await response.json();
      if (!response.ok) throw payload;
      updateProductRow(payload);
      modal.hide();
    } catch (payload) {
      const fallback = { general: [{ message: 'No se pudo actualizar el producto.' }] };
      const messages = Object.values(payload.errors || fallback).flat().map((item) => item.message);
      errors.textContent = messages.join(' ');
      errors.classList.remove('d-none');
    } finally {
      saveButton.disabled = false;
      saveButton.innerHTML = '<i class="bi bi-check2"></i> Guardar';
    }
  });

  function updateProductRow(product) {
    const row = document.querySelector(`[data-product-id="${product.id}"]`);
    if (!row) return;
    row.querySelector('[data-field="nombre"]').textContent = product.nombre;
    row.querySelector('[data-field="descripcion"]').textContent = product.descripcion;
    row.querySelector('[data-field="precio"]').textContent = '$' + product.precio_base;
    const status = row.querySelector('[data-field="estado"]');
    status.textContent = product.activo ? 'Activo' : 'Inactivo';
    status.className = 'badge-status ' + (product.activo ? 'badge-active' : 'badge-inactive');
    const thumb = row.querySelector('[data-field="imagen"]');
    thumb.innerHTML = product.imagen_url ? `<img src="${escapeHtml(product.imagen_url)}" class="product-thumb" alt="${escapeHtml(product.nombre)}">` : '<div class="product-thumb d-flex align-items-center justify-content-center" style="color:var(--fersit-navy);"><i class="bi bi-box-seam fs-4"></i></div>';
    const button = row.querySelector('.js-edit-product');
    button.dataset.nombre = product.nombre;
    button.dataset.descripcion = product.descripcion;
    button.dataset.precio = product.precio_base;
    button.dataset.activo = product.activo;
    button.dataset.imagen = product.imagen_url;
  }

  function hideErrors() {
    errors.classList.add('d-none');
    errors.textContent = '';
  }
});
