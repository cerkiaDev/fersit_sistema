(function () {
    "use strict";

    function parseNumber(value) {
        var normalized = (value || "").toString().replace(",", ".");
        var number = parseFloat(normalized);
        return Number.isFinite(number) ? number : 0;
    }

    function formatMoney(value) {
        return value.toFixed(2);
    }

    function keepInteger(input) {
        var value = input.value || "";
        var separatorIndex = value.search(/[.,]/);

        if (separatorIndex !== -1) {
            input.value = value.slice(0, separatorIndex);
        }
    }

    function closestContainer(element) {
        return element.closest("tr") || element.closest("fieldset") || document;
    }

    function field(container, suffix) {
        return (
            container.querySelector("[name$='-" + suffix + "']") ||
            container.querySelector("[name='" + suffix + "']")
        );
    }

    function subtotalTarget(container) {
        return (
            container.querySelector(".field-subtotal .readonly") ||
            container.querySelector(".field-subtotal p") ||
            container.querySelector(".field-subtotal")
        );
    }

    function updateSubtotal(container) {
        var cantidad = field(container, "cantidad");
        var precio = field(container, "precio_extra");
        var target = subtotalTarget(container);

        if (!cantidad || !precio || !target) {
            return;
        }

        target.textContent = formatMoney(
            parseNumber(cantidad.value) * parseNumber(precio.value)
        );
    }

    function fillPriceFromProduct(container, force) {
        var producto = field(container, "producto");
        var precio = field(container, "precio_extra");

        if (!producto || !precio) {
            return;
        }

        var selected = producto.options[producto.selectedIndex];
        var productPrice = selected ? selected.dataset.precio : "";

        if (productPrice && (force || !precio.value)) {
            precio.value = formatMoney(parseNumber(productPrice));
        }
    }

    function setup(container) {
        if (container.dataset && container.dataset.detalleCotizacionReady) {
            return;
        }

        var producto = field(container, "producto");
        var cantidad = field(container, "cantidad");
        var precio = field(container, "precio_extra");
        var tipoMedida = field(container, "tipo_medida");

        if (!cantidad || !precio) {
            return;
        }

        if (container.dataset) {
            container.dataset.detalleCotizacionReady = "true";
        }

        if (producto) {
            producto.addEventListener("change", function () {
                fillPriceFromProduct(container, true);
                updateSubtotal(container);
            });
        }

        if (tipoMedida) {
            tipoMedida.addEventListener("change", function () {
                fillPriceFromProduct(container, false);
                updateSubtotal(container);
            });
        }

        cantidad.addEventListener("input", function () {
            keepInteger(cantidad);
            updateSubtotal(container);
        });
        precio.addEventListener("input", function () {
            updateSubtotal(container);
        });

        fillPriceFromProduct(container, false);
        keepInteger(cantidad);
        updateSubtotal(container);
    }

    function setupAll(root) {
        var seen = [];

        root.querySelectorAll("[name$='-precio_extra'], [name='precio_extra']").forEach(
            function (input) {
                var container = closestContainer(input);

                if (seen.indexOf(container) === -1) {
                    seen.push(container);
                    setup(container);
                }
            }
        );
    }

    document.addEventListener("DOMContentLoaded", function () {
        setupAll(document);

        document.addEventListener("formset:added", function (event) {
            setup(event.target);
        });

        if (window.django && window.django.jQuery) {
            window.django.jQuery(document).on("formset:added", function (event, row) {
                setup(row);
            });
        }
    });
})();
