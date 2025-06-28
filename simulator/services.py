import decimal
from typing import Dict, List, Any

from .models import CreditProfile

# Usamos el tipo Decimal para todos los cálculos monetarios para evitar errores de precisión.
D = decimal.Decimal

class LoanCalculatorService:
    """
    Servicio para encapsular toda la lógica de cálculo de un préstamo.
    """
    def __init__(self, profile: CreditProfile, amount: D, term: int):
        self.profile = profile
        self.amount_requested = D(amount)
        self.term_months = int(term)
        self.monthly_interest_rate = D(self.profile.interest_rate / 100)

    def calculate_loan_details(self) -> Dict[str, Any]:
        """
        Orquesta el cálculo completo del préstamo.
        Retorna un diccionario con todos los resultados.
        """
        charges_breakdown = self._calculate_additional_charges()
        
        total_additional_charges = sum(charges_breakdown.values())
        total_loan_amount = self.amount_requested + total_additional_charges
        
        monthly_payment = self._calculate_monthly_payment(total_loan_amount)
        
        amortization_table = self._generate_amortization_table(total_loan_amount, monthly_payment)

        return {
            "disbursed_amount": self.amount_requested,
            "total_loan_amount": total_loan_amount,
            "monthly_payment": monthly_payment,
            "charges_breakdown": {
                "guarantee": charges_breakdown["guarantee"],
                "guarantee_vat": charges_breakdown["guarantee_vat"],
                "grace_period_interest": charges_breakdown["grace_period_interest"],
                "insurance": charges_breakdown["insurance"],
                "broker_commission": charges_breakdown["broker_commission"],
            },
            "amortization_table": amortization_table,
        }

    def _calculate_additional_charges(self) -> Dict[str, D]:
        """Calcula cada uno de los cargos adicionales basados en el perfil."""
        guarantee_value = self.amount_requested * (D(self.profile.guarantee_percentage) / 100)
        guarantee_vat_value = guarantee_value * (D(self.profile.guarantee_vat_percentage) / 100)
        grace_interest_value = self.amount_requested * self.monthly_interest_rate / 30 * D(self.profile.grace_period_days)
        insurance_value = self.amount_requested * (D(self.profile.insurance_percentage) / 100)
        broker_commission_value = self.amount_requested * (D(self.profile.broker_commission_percentage) / 100)

        return {
            "guarantee": guarantee_value,
            "guarantee_vat": guarantee_vat_value,
            "grace_period_interest": grace_interest_value,
            "insurance": insurance_value,
            "broker_commission": broker_commission_value,
        }

    def _calculate_monthly_payment(self, total_loan_amount: D) -> D:
        """Calcula la cuota fija mensual usando la fórmula de amortización francesa."""
        if self.monthly_interest_rate == 0:
            return total_loan_amount / self.term_months

        i = self.monthly_interest_rate
        n = self.term_months
        
        # Fórmula: P * [i(1+i)^n] / [(1+i)^n - 1]
        numerator = i * ((1 + i) ** n)
        denominator = ((1 + i) ** n) - 1
        monthly_payment = total_loan_amount * (numerator / denominator)
        
        return monthly_payment.quantize(D('0.01'), rounding=decimal.ROUND_HALF_UP)

    def _generate_amortization_table(self, total_loan_amount: D, monthly_payment: D) -> List[Dict[str, Any]]:
        """Genera la tabla de amortización completa."""
        table = []
        outstanding_balance = total_loan_amount

        for period in range(1, self.term_months + 1):
            interest_payment = outstanding_balance * self.monthly_interest_rate
            principal_payment = monthly_payment - interest_payment
            final_balance = outstanding_balance - principal_payment
            
            # Asegurar que la última cuota salde el crédito exactamente
            if period == self.term_months:
                principal_payment += final_balance
                monthly_payment = interest_payment + principal_payment
                final_balance = D(0)

            table.append({
                "period": period,
                "initial_balance": outstanding_balance,
                "monthly_payment": monthly_payment,
                "interest": interest_payment,
                "principal": principal_payment,
                "final_balance": final_balance,
            })
            outstanding_balance = final_balance
        
        return table