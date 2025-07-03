document.addEventListener('DOMContentLoaded', () => {
    const loanForm = document.getElementById('loan-form');
    if (!loanForm) return;

    // Variable para guardar los datos de la última simulación exitosa
    let lastCalculationInputs = null;

    const csrfToken = loanForm.querySelector('[name=csrfmiddlewaretoken]').value;
    const loadingIndicator = document.getElementById('loading-indicator');
    const excelButton = document.getElementById('download-excel');
    const pdfButton = document.getElementById('download-pdf');
    const calculateBtn = document.getElementById('calculate-btn');

    // Formateo de moneda mejorado
    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency', 
            currency: 'COP', 
            minimumFractionDigits: 0, 
            maximumFractionDigits: 0
        }).format(amount);
    };

    // Función para mostrar/ocultar loading
    const toggleLoading = (show) => {
        if (loadingIndicator) {
            loadingIndicator.classList.toggle('hidden', !show);
        }
        if (calculateBtn) {
            calculateBtn.disabled = show;
            calculateBtn.innerHTML = show 
                ? '<div class="spinner" style="width: 16px; height: 16px; margin-right: 8px;"></div> Calculando...'
                : '<i class="fas fa-calculator"></i> Calcular Simulación';
        }
    };

    // Función para mostrar errores
    const showError = (message) => {
        // Crear o actualizar alert de error
        let errorAlert = document.querySelector('.alert-error');
        if (!errorAlert) {
            errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-error mb-6 animate-fade-in';
            errorAlert.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <span></span>
            `;
            loanForm.parentNode.insertBefore(errorAlert, loanForm);
        }
        errorAlert.querySelector('span').textContent = message;
        errorAlert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Auto-hide después de 5 segundos
        setTimeout(() => {
            if (errorAlert) {
                errorAlert.style.opacity = '0';
                setTimeout(() => errorAlert.remove(), 300);
            }
        }, 5000);
    };

    // Función para validar formulario
    const validateForm = () => {
        const profileId = document.getElementById('profile').value;
        const amount = document.getElementById('amount').value;
        const term = document.getElementById('term').value;

        // Limpiar errores previos
        document.querySelectorAll('.error-message').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.form-control').forEach(el => el.style.borderColor = '');

        let isValid = true;

        if (!profileId) {
            showFieldError('profile', 'Por favor seleccione un perfil');
            isValid = false;
        }

        if (!amount || amount <= 0) {
            showFieldError('amount', 'Ingrese un monto válido mayor a 0');
            isValid = false;
        }

        if (!term || term <= 0) {
            showFieldError('term', 'Ingrese un plazo válido mayor a 0');
            isValid = false;
        }

        return isValid;
    };

    const showFieldError = (fieldId, message) => {
        const field = document.getElementById(fieldId);
        const errorElement = field.parentNode.querySelector('.error-message');
        
        if (field) {
            field.style.borderColor = 'var(--error-color)';
        }
        
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        }
    };

    // Event listener para el formulario
    loanForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        const profileId = document.getElementById('profile').value;
        const amount = document.getElementById('amount').value;
        const term = document.getElementById('term').value;

        toggleLoading(true);
        document.getElementById('results-section').classList.add('hidden');
        
        // Desactivar botones de exportación
        if (excelButton) excelButton.disabled = true;
        if (pdfButton) pdfButton.disabled = true;

        try {
            const response = await fetch('/calculate/', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'X-CSRFToken': csrfToken 
                },
                body: JSON.stringify({ 
                    profile_id: profileId, 
                    amount: amount, 
                    term: term 
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || 'Ocurrió un error en el servidor.');
            }
            
            const results = await response.json();
            
            // Guardar inputs y actualizar UI
            lastCalculationInputs = { profileId, amount, term };
            updateUI(results);

            // Activar botones de exportación
            if (excelButton) excelButton.disabled = false;
            if (pdfButton) pdfButton.disabled = false;

        } catch (error) {
            console.error('Error en el cálculo:', error);
            showError(`Error: ${error.message}`);
        } finally {
            toggleLoading(false);
        }
    });

    function updateUI(data) {
        // Actualizar tarjetas de resumen con animación
        const updateElement = (id, value) => {
            const element = document.getElementById(id);
            if (element) {
                element.style.opacity = '0';
                setTimeout(() => {
                    element.textContent = formatCurrency(value);
                    element.style.opacity = '1';
                }, 150);
            }
        };

        updateElement('total-loan', data.total_loan_amount);
        updateElement('monthly-payment', data.monthly_payment);
        updateElement('disbursed-amount', data.disbursed_amount);

        // Actualizar desglose de cargos
        const chargesBreakdown = document.getElementById('charges-breakdown');
        if (chargesBreakdown) {
            const breakdown = data.charges_breakdown;
            updateElement('guarantee-value', breakdown.guarantee);
            updateElement('guarantee-vat-value', breakdown.guarantee_vat);
            updateElement('grace-value', breakdown.grace_period_interest);
            updateElement('insurance-value', breakdown.insurance);
            updateElement('broker-value', breakdown.broker_commission);
        }
        
        // Actualizar tabla de amortización
        const amortizationTableBody = document.getElementById('amortization-table');
        if (amortizationTableBody) {
            amortizationTableBody.innerHTML = '';
            
            data.amortization_table.forEach((row, index) => {
                const tr = document.createElement('tr');
                tr.style.opacity = '0';
                tr.innerHTML = `
                    <td style="text-align: center; font-weight: var(--font-semibold); color: var(--primary-text);">
                        ${row.period}
                    </td>
                    <td>${formatCurrency(row.initial_balance)}</td>
                    <td>${formatCurrency(row.interest)}</td>
                    <td style="font-weight: var(--font-semibold); color: var(--primary-text);">
                        ${formatCurrency(row.monthly_payment)}
                    </td>
                    <td>${formatCurrency(row.principal)}</td>
                    <td style="font-weight: var(--font-semibold); color: var(--accent-blue);">
                        ${formatCurrency(row.final_balance)}
                    </td>
                `;
                amortizationTableBody.appendChild(tr);
                
                // Animación de aparición escalonada
                setTimeout(() => {
                    tr.style.transition = 'opacity 0.3s ease';
                    tr.style.opacity = '1';
                }, index * 50);
            });
        }

        // Mostrar sección de resultados con animación
        const resultsSection = document.getElementById('results-section');
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Lógica de los botones de exportación
    function handleExport(exportType) {
        if (!lastCalculationInputs) {
            showError('Por favor, primero realice un cálculo.');
            return;
        }
        
        const { profileId, amount, term } = lastCalculationInputs;
        const url = new URL(`${window.location.origin}/export/${exportType}/`);
        url.searchParams.append('profile_id', profileId);
        url.searchParams.append('amount', amount);
        url.searchParams.append('term', term);
        
        // Crear enlace temporal para descarga
        const link = document.createElement('a');
        link.href = url.toString();
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Event listeners para botones de exportación
    if (excelButton) {
        excelButton.addEventListener('click', () => handleExport('excel'));
    }
    
    if (pdfButton) {
        pdfButton.addEventListener('click', () => handleExport('pdf'));
    }

    // Mejorar UX de los inputs
    document.querySelectorAll('.form-control').forEach(input => {
        input.addEventListener('focus', () => {
            input.style.borderColor = 'var(--accent-blue)';
            input.style.boxShadow = '0 0 0 3px rgba(66, 89, 237, 0.1)';
        });

        input.addEventListener('blur', () => {
            input.style.borderColor = '';
            input.style.boxShadow = '';
        });

        input.addEventListener('input', () => {
            // Limpiar errores cuando el usuario empiece a escribir
            const errorElement = input.parentNode.querySelector('.error-message');
            if (errorElement) {
                errorElement.classList.add('hidden');
            }
            input.style.borderColor = '';
        });
    });

    // Formateo automático del campo de monto
    const amountInput = document.getElementById('amount');
    if (amountInput) {
        amountInput.addEventListener('input', (e) => {
            // Remover caracteres no numéricos excepto punto decimal
            let value = e.target.value.replace(/[^\d.]/g, '');
            
            // Asegurar solo un punto decimal
            const parts = value.split('.');
            if (parts.length > 2) {
                value = parts[0] + '.' + parts.slice(1).join('');
            }
            
            e.target.value = value;
        });
    }
});