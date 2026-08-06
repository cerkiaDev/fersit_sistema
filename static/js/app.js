/* FERSIT ALARMAS - Scripts globales */

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.sidebar-toggle');
  const sidebar = document.querySelector('.admin-sidebar');
  const backdrop = document.querySelector('.sidebar-backdrop');

  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('show');
      backdrop?.classList.toggle('show');
    });
    backdrop?.addEventListener('click', () => {
      sidebar.classList.remove('show');
      backdrop.classList.remove('show');
    });
  }

  if (document.getElementById('quoteLinesBody')) initQuoteEditor();
});

function initQuoteEditor() {
  const tbody = document.getElementById('quoteLinesBody');
  const addBtn = document.getElementById('addQuoteLine');
  const ivaRate = document.getElementById('ivaRate');

  addBtn?.addEventListener('click', () => addQuoteLine());
  tbody?.addEventListener('input', recalcTotals);
  tbody?.addEventListener('change', recalcTotals);
  ['input', 'change', 'blur'].forEach((eventName) => {
    ivaRate?.addEventListener(eventName, recalcTotals);
  });
  tbody?.addEventListener('click', (event) => {
    const btn = event.target.closest('.btn-remove-row');
    if (!btn) return;
    btn.closest('tr').remove();
    renumberQuoteLines();
    recalcTotals();
  });

  tbody?.querySelectorAll('.line-product').forEach(bindProductPrice);
  tbody?.querySelectorAll('.line-measure').forEach(bindMeasureLabel);

  if (tbody && tbody.children.length === 0) addQuoteLine();
  recalcTotals();
}

function addQuoteLine() {
  const tbody = document.getElementById('quoteLinesBody');
  const idx = tbody.children.length + 1;
  const options = document.getElementById('productOptionsTemplate')?.innerHTML || '<option value="">-- Concepto libre --</option>';
  const tr = document.createElement('tr');

  tr.innerHTML = `
    <td class="text-muted">${idx}</td>
    <td>
      <div class="quote-product-cell">
        <div class="quote-product-thumb is-empty"><i class="bi bi-image"></i></div>
        <div class="quote-product-fields">
          <select name="producto" class="form-select form-select-sm line-product">
            ${options}
          </select>
          <input name="concepto" type="text" class="form-control form-control-sm mt-1 line-concept" placeholder="Ej: Instalacion, mano de obra...">
        </div>
      </div>
    </td>
    <td>
      <select name="tipo_medida" class="form-select form-select-sm line-measure">
        <option value="unidad">Unidad</option>
        <option value="metro">Metro</option>
      </select>
    </td>
    <td class="text-muted small line-measure-label">Unidad</td>
    <td><input name="cantidad" type="number" step="1" class="form-control form-control-sm line-qty" value="1" min="1"></td>
    <td><input name="precio_unitario" type="number" step="0.01" class="form-control form-control-sm line-price" value="0.00" min="0"></td>
    <td class="text-end fw-semibold line-subtotal">$0.00</td>
    <td class="text-center"><button type="button" class="btn-remove-row" title="Eliminar"><i class="bi bi-trash"></i></button></td>
  `;

  tbody.appendChild(tr);
  bindProductPrice(tr.querySelector('.line-product'));
  updateProductThumb(tr.querySelector('.line-product'));
  bindMeasureLabel(tr.querySelector('.line-measure'));
  recalcTotals();
}

function bindProductPrice(select) {
  select?.addEventListener('change', (event) => {
    const row = event.target.closest('tr');
    const opt = event.target.selectedOptions[0];
    const price = opt?.dataset.price;
    if (price) row.querySelector('.line-price').value = parseFloat(price).toFixed(2);
    updateProductThumb(event.target);
    recalcTotals();
  });
  updateProductThumb(select);
}

function updateProductThumb(select) {
  const row = select?.closest('tr');
  const thumb = row?.querySelector('.quote-product-thumb');
  if (!thumb) return;

  const imageUrl = select.selectedOptions[0]?.dataset.image || '';
  if (!imageUrl) {
    thumb.classList.add('is-empty');
    thumb.innerHTML = '<i class="bi bi-image"></i>';
    return;
  }

  const label = select.selectedOptions[0]?.textContent || 'Producto';
  thumb.classList.remove('is-empty');
  thumb.innerHTML = `<img src="${imageUrl}" alt="${escapeHtml(label)}">`;
}

function bindMeasureLabel(select) {
  select?.addEventListener('change', (event) => {
    const row = event.target.closest('tr');
    const label = event.target.selectedOptions[0]?.textContent || '';
    row.querySelector('.line-measure-label').textContent = label;
  });
}

function recalcTotals() {
  let subtotal = 0;

  document.querySelectorAll('#quoteLinesBody tr').forEach((tr) => {
    const qtyInput = tr.querySelector('.line-qty');
    if (qtyInput && qtyInput.value) {
      qtyInput.value = String(Math.max(1, parseInt(qtyInput.value, 10) || 1));
    }

    const qty = parseFloat(qtyInput?.value) || 0;
    const price = parseFloat(tr.querySelector('.line-price')?.value) || 0;
    const line = qty * price;
    tr.querySelector('.line-subtotal').textContent = '$' + line.toFixed(2);
    subtotal += line;
  });

  const ivaRate = Math.max(0, Math.min(100, parseFloat(document.getElementById('ivaRate')?.value) || 0));
  const iva = subtotal * (ivaRate / 100);
  const total = subtotal + iva;
  setText('totSubtotal', '$' + subtotal.toFixed(2));
  setText('ivaLabel', 'IVA (' + ivaRate.toFixed(2) + '%)');
  setText('totIva', '$' + iva.toFixed(2));
  setText('totGrand', '$' + total.toFixed(2));
}

function renumberQuoteLines() {
  document.querySelectorAll('#quoteLinesBody tr').forEach((tr, index) => {
    tr.children[0].textContent = index + 1;
  });
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
