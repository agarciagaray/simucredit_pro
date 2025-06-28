document.addEventListener('DOMContentLoaded', () => {

    const loanForm = document.getElementById('loan-form');
    if (!loanForm) return;

    // Variable para guardar los datos de la última simulación exitosa
    let lastCalculationInputs = null;

    const csrfToken = loanForm.querySelector('[name=csrfmiddlewaretoken]').value;
    const loadingIndicator = document.getElementById('loading-indicator');
    const excelButton = document.getElementById('download-excel');
    const pdfButton = document.getElementById('download-pdf');

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency', currency: 'COP', minimumFractionDigits: 2, maximumFractionDigits: 2
        }).format(amount);
    };

    loanForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const profileId = document.getElementById('profile').value;
        const amount = document.getElementById('amount').value;
        const term = document.getElementById('term').value;

        if (!profileId || !amount || !term || amount <= 0 || term <= 0) {
            alert('Por favor, complete todos los campos con valores válidos.');
            return;
        }

        loadingIndicator.classList.remove('hidden');
        document.getElementById('results-section').classList.add('hidden');
        // Desactivamos los botones de exportación mientras se calcula
        if(excelButton) excelButton.disabled = true;
        if(pdfButton) pdfButton.disabled = true;

        try {
            const response = await fetch('/calculate/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ profile_id: profileId, amount: amount, term: term })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || 'Ocurrió un error en el servidor.');
            }
            const results = await response.json();
            
            // Guardamos los inputs y actualizamos la UI
            lastCalculationInputs = { profileId, amount, term };
            updateUI(results);

            // Activamos los botones de exportación
            if(excelButton) excelButton.disabled = false;
            if(pdfButton) pdfButton.disabled = false;

        } catch (error) {
            console.error('Error en el cálculo:', error);
            alert(`Error: ${error.message}`);
        } finally {
            loadingIndicator.classList.add('hidden');
        }
    });

    function updateUI(data) {
        document.getElementById('total-loan').textContent = formatCurrency(data.total_loan_amount);
        document.getElementById('monthly-payment').textContent = formatCurrency(data.monthly_payment);
        document.getElementById('disbursed-amount').textContent = formatCurrency(data.disbursed_amount);

        const chargesBreakdown = document.getElementById('charges-breakdown');
        if (chargesBreakdown) {
            const breakdown = data.charges_breakdown;
            document.getElementById('guarantee-value').textContent = formatCurrency(breakdown.guarantee);
            document.getElementById('guarantee-vat-value').textContent = formatCurrency(breakdown.guarantee_vat);
            document.getElementById('grace-value').textContent = formatCurrency(breakdown.grace_period_interest);
            document.getElementById('insurance-value').textContent = formatCurrency(breakdown.insurance);
            document.getElementById('broker-value').textContent = formatCurrency(breakdown.broker_commission);
        }
        
        const amortizationTableBody = document.getElementById('amortization-table');
        if (amortizationTableBody) {
            amortizationTableBody.innerHTML = '';
            data.amortization_table.forEach(row => {
                const tr = document.createElement('tr');
                tr.classList.add(row.period % 2 === 0 ? 'bg-gray-50' : 'bg-white');
                tr.innerHTML = `
                    <td class="px-4 py-2">${row.period}</td>
                    <td class="px-4 py-2">${formatCurrency(row.initial_balance)}</td>
                    <td class="px-4 py-2">${formatCurrency(row.interest)}</td>
                    <td class="px-4 py-2">${formatCurrency(row.monthly_payment)}</td>
                    <td class="px-4 py-2">${formatCurrency(row.principal)}</td>
                    <td class="px-4 py-2">${formatCurrency(row.final_balance)}</td>
                `;
                amortizationTableBody.appendChild(tr);
            });
        }
        const resultsSection = document.getElementById('results-section');
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Lógica de los botones de exportación
    function handleExport(exportType) {
        if (!lastCalculationInputs) {
            alert('Por favor, primero realice un cálculo.');
            return;
        }
        const { profileId, amount, term } = lastCalculationInputs;
        const url = new URL(`${window.location.origin}/export/${exportType}/`);
        url.searchParams.append('profile_id', profileId);
        url.searchParams.append('amount', amount);
        url.searchParams.append('term', term);
        
        // Redirigir para iniciar la descarga
        window.location.href = url.toString();
    }

    if(excelButton) excelButton.addEventListener('click', () => handleExport('excel'));
    if(pdfButton) pdfButton.addEventListener('click', () => handleExport('pdf'));
});