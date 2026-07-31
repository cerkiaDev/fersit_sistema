/* FERSIT ALARMAS - Scripts globales */

// Toggle sidebar en móvil
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

  // Inicializar editor de cotización si existe
  if (document.getElementById('quoteLinesBody')) initQuoteEditor();
});

/* ============================================
   EDITOR DE COTIZACIÓN (ERP-style)
   ============================================ */
const PRODUCTS_DEMO = [
  { id: 1, name: 'Alarma Residencial Básica', price: 250.00 },
  { id: 2, name: 'Cámara IP HD Exterior',     price: 120.00 },
  { id: 3, name: 'Sensor de Movimiento PIR',  price: 35.00 },
  { id: 4, name: 'Panel de Control Inalámbrico', price: 180.00 },
  { id: 5, name: 'Sirena Exterior 30W',       price: 65.00 },
];

function initQuoteEditor() {
  const tbody = document.getElementById('quoteLinesBody');
  const addBtn = document.getElementById('addQuoteLine');

  addBtn?.addEventListener('click', () => addQuoteLine());
  tbody?.addEventListener('input', recalcTotals);
  tbody?.addEventListener('change', recalcTotals);
  tbody?.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-remove-row');
    if (btn) { btn.closest('tr').remove(); recalcTotals(); }
  });

  // Agregar 2 filas iniciales de ejemplo
  addQuoteLine(); addQuoteLine();
}

function addQuoteLine() {
  const tbody = document.getElementById('quoteLinesBody');
  const idx = tbody.children.length + 1;
  const options = PRODUCTS_DEMO.map(p => `<option value="${p.id}" data-price="${p.price}">${p.name}</option>`).join('');
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td class="text-muted">${idx}</td>
    <td>
      <select class="form-select form-select-sm line-product">
        <option value="">-- Concepto libre --</option>
        ${options}
      </select>
      <input type="text" class="form-control form-control-sm mt-1 line-concept" placeholder="Ej: Instalación, mano de obra...">
    </td>
    <td>
      <select class="form-select form-select-sm line-measure">
        <option>Unidad</option><option>Metro</option><option>Servicio</option><option>Hora</option>
      </select>
    </td>
    <td><input type="text" class="form-control form-control-sm line-unit" placeholder="u / m"></td>
    <td><input type="number" step="0.01" class="form-control form-control-sm line-qty" value="1" min="0"></td>
    <td><input type="number" step="0.01" class="form-control form-control-sm line-price" value="0.00" min="0"></td>
    <td class="text-end fw-semibold line-subtotal">$0.00</td>
    <td class="text-center"><button class="btn-remove-row" title="Eliminar"><i class="bi bi-trash"></i></button></td>
  `;
  tbody.appendChild(tr);

  // Auto-precio al elegir producto
  tr.querySelector('.line-product').addEventListener('change', (e) => {
    const opt = e.target.selectedOptions[0];
    const price = opt?.dataset.price;
    if (price) tr.querySelector('.line-price').value = parseFloat(price).toFixed(2);
    recalcTotals();
  });
  recalcTotals();
}

function recalcTotals() {
  let subtotal = 0;
  document.querySelectorAll('#quoteLinesBody tr').forEach(tr => {
    const qty   = parseFloat(tr.querySelector('.line-qty')?.value)   || 0;
    const price = parseFloat(tr.querySelector('.line-price')?.value) || 0;
    const line  = qty * price;
    tr.querySelector('.line-subtotal').textContent = '$' + line.toFixed(2);
    subtotal += line;
  });
  const iva = subtotal * 0.15;
  const total = subtotal + iva;
  setText('totSubtotal', '$' + subtotal.toFixed(2));
  setText('totIva',      '$' + iva.toFixed(2));
  setText('totGrand',    '$' + total.toFixed(2));
}
function setText(id, v) { const el = document.getElementById(id); if (el) el.textContent = v; }
