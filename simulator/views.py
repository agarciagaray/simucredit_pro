import decimal
import io
import json
from datetime import datetime

import pandas as pd
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from weasyprint import HTML

from .models import CreditProfile
from .services import LoanCalculatorService


# ... (simulator_view, calculate_loan_view, logout_view sin cambios) ...
@login_required
def simulator_view(request):
    """
    Renderiza la página principal del simulador de crédito.
    """
    credit_profiles = CreditProfile.objects.filter(deleted_at__isnull=True)
    user_role = 'ADMIN' if request.user.is_staff else 'USER'
    context = {
        'credit_profiles': credit_profiles,
        'user_role': user_role
    }
    return render(request, 'simulator.html', context)


def convert_decimals(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    return obj


@login_required
@require_POST
def calculate_loan_view(request):
    """
    Endpoint para calcular los detalles del préstamo.
    Recibe los datos vía POST (JSON) y devuelve los resultados en JSON.
    """
    try:
        data = json.loads(request.body)
        profile_id = data.get('profile_id')
        amount = decimal.Decimal(data.get('amount'))
        term = int(data.get('term'))
        if not all([profile_id, amount, term]) or amount <= 0 or term <= 0:
            return HttpResponseBadRequest("Datos de entrada inválidos.")
        profile = CreditProfile.objects.get(id=profile_id)
        service = LoanCalculatorService(
            profile=profile, amount=amount, term=term)
        results = service.calculate_loan_details()

        return JsonResponse(convert_decimals(results))
    except (json.JSONDecodeError, KeyError, ValueError, CreditProfile.DoesNotExist) as e:
        return HttpResponseBadRequest(f"Error en la solicitud: {e}")
    except Exception as e:
        return JsonResponse({'error': f'Ocurrió un error inesperado: {e}'}, status=500)


@staff_member_required
@require_GET
def export_excel_view(request):
    """
    Genera y devuelve un archivo Excel con el resumen del crédito y la tabla de amortización en hojas separadas.
    """
    try:
        profile_id = request.GET.get('profile_id')
        amount = decimal.Decimal(request.GET.get('amount'))
        term = int(request.GET.get('term'))

        profile = CreditProfile.objects.get(id=profile_id)
        service = LoanCalculatorService(
            profile=profile, amount=amount, term=term)
        results = service.calculate_loan_details()

        # --- Hoja de Resumen ---
        charges = results['charges_breakdown']
        summary_data = {
            'Concepto': [
                'Monto Desembolsado',
                'Monto Total del Préstamo',
                'Cuota Fija Mensual',
                '---',
                'Desglose de Cargos Adicionales',
                'Afianzamiento',
                'IVA del Afianzamiento',
                'Interés de Carencia',
                'Seguro',
                'Comisión del Corredor'
            ],
            'Valor': [
                results['disbursed_amount'],
                results['total_loan_amount'],
                results['monthly_payment'],
                '---',
                '---',
                charges['guarantee'],
                charges['guarantee_vat'],
                charges['grace_period_interest'],
                charges['insurance'],
                charges['broker_commission']
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary['Valor'] = df_summary['Valor'].apply(
            lambda x: f"${float(x):,.2f}" if isinstance(
                x, decimal.Decimal) else x
        )

        # --- Hoja de Amortización ---
        amortization_data = results['amortization_table']
        df_amortization = pd.DataFrame(amortization_data)
        for col in ['initial_balance', 'interest', 'monthly_payment', 'principal', 'final_balance']:
            df_amortization[col] = df_amortization[col].apply(
                lambda x: float(x))

        df_amortization.rename(columns={
            'period': 'Periodo', 'initial_balance': 'Saldo Inicial', 'interest': 'Interés',
            'monthly_payment': 'Cuota', 'principal': 'Amortización', 'final_balance': 'Saldo Final'
        }, inplace=True)

        # --- Escribir en el buffer de Excel ---
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_summary.to_excel(writer, index=False,
                                sheet_name='ResumenCredito')
            df_amortization.to_excel(
                writer, index=False, sheet_name='TablaAmortizacion')

            workbook = writer.book
            worksheet_summary = writer.sheets['ResumenCredito']
            for col in worksheet_summary.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet_summary.column_dimensions[column].width = adjusted_width

            worksheet_amortization = writer.sheets['TablaAmortizacion']
            for col in worksheet_amortization.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet_amortization.column_dimensions[column].width = adjusted_width

            # Aplicar formato de moneda a la hoja de amortización
            currency_format = '$ #,##0.00'
            for col_letter in ['B', 'C', 'D', 'E', 'F']:
                for cell in worksheet_amortization[col_letter]:
                    cell.number_format = currency_format

        buffer.seek(0)
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"ReporteCredito_{datetime.now().strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except (KeyError, ValueError, CreditProfile.DoesNotExist) as e:
        return HttpResponseBadRequest(f"Parámetros inválidos para exportar: {e}")


@staff_member_required
@require_GET
def export_pdf_view(request):
    """
    Genera y devuelve un reporte PDF con el resumen completo del crédito.
    """
    try:
        profile_id = request.GET.get('profile_id')
        amount = decimal.Decimal(request.GET.get('amount'))
        term = int(request.GET.get('term'))

        profile = CreditProfile.objects.get(id=profile_id)
        service = LoanCalculatorService(
            profile=profile, amount=amount, term=term)
        results = service.calculate_loan_details()

        context = {
            'profile': profile,
            'term': term,
            'results': results
        }

        # Renderizar la plantilla HTML a un string
        html_string = render_to_string('report.html', context)

        # Generar el PDF
        pdf_file = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        filename = f"Reporte_Credito_{datetime.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except (KeyError, ValueError, CreditProfile.DoesNotExist) as e:
        return HttpResponseBadRequest(f"Parámetros inválidos para exportar: {e}")


def logout_view(request):
    logout(request)
    return redirect('login')


# Vista para listar y crear perfiles de crédito
@staff_member_required
def credit_profiles_list(request):
    profiles = CreditProfile.objects.filter(deleted_at__isnull=True)
    return render(request, 'perfiles.html', {'profiles': profiles})


@staff_member_required
@csrf_exempt
def credit_profile_create(request):
    if request.method == 'POST':
        data = request.POST
        name = data.get('name')

        def parse_decimal(val):
            return decimal.Decimal(val) if val not in (None, '', 'None') else None

        def parse_int(val):
            return int(val) if val not in (None, '', 'None') else None
        if CreditProfile.objects.filter(name=name, deleted_at__isnull=True).exists():
            profiles = CreditProfile.objects.filter(deleted_at__isnull=True)
            error = f'Ya existe un perfil activo con el nombre "{name}".'
            return render(request, 'perfiles.html', {'profiles': profiles, 'error': error})
        profile = CreditProfile.objects.create(
            name=name,
            interest_rate=parse_decimal(data.get('interest_rate')),
            guarantee_percentage=parse_decimal(
                data.get('guarantee_percentage')),
            guarantee_vat_percentage=parse_decimal(
                data.get('guarantee_vat_percentage')),
            grace_period_days=parse_int(data.get('grace_period_days')),
            insurance_percentage=parse_decimal(
                data.get('insurance_percentage')),
            broker_commission_percentage=parse_decimal(
                data.get('broker_commission_percentage')),
        )
        return redirect(reverse('credit_profiles_list'))
    return HttpResponseBadRequest('Método no permitido')


@staff_member_required
@csrf_exempt
def credit_profile_edit(request, pk):
    try:
        profile = CreditProfile.objects.get(pk=pk, deleted_at__isnull=True)
    except CreditProfile.DoesNotExist:
        return HttpResponseBadRequest('Perfil no encontrado')
    if request.method == 'POST':
        data = request.POST

        def parse_decimal(val):
            return decimal.Decimal(val) if val not in (None, '', 'None') else None

        def parse_int(val):
            return int(val) if val not in (None, '', 'None') else None
        profile.name = data.get('name')
        profile.interest_rate = parse_decimal(data.get('interest_rate'))
        profile.guarantee_percentage = parse_decimal(
            data.get('guarantee_percentage'))
        profile.guarantee_vat_percentage = parse_decimal(
            data.get('guarantee_vat_percentage'))
        profile.grace_period_days = parse_int(data.get('grace_period_days'))
        profile.insurance_percentage = parse_decimal(
            data.get('insurance_percentage'))
        profile.broker_commission_percentage = parse_decimal(
            data.get('broker_commission_percentage'))
        profile.save()
        return redirect(reverse('credit_profiles_list'))
    return HttpResponseBadRequest('Método no permitido')


@staff_member_required
@csrf_exempt
def credit_profile_delete(request, pk):
    try:
        profile = CreditProfile.objects.get(pk=pk, deleted_at__isnull=True)
    except CreditProfile.DoesNotExist:
        return HttpResponseBadRequest('Perfil no encontrado')
    if request.method == 'POST':
        profile.delete()
        return redirect(reverse('credit_profiles_list'))
    return HttpResponseBadRequest('Método no permitido')


@staff_member_required
def users_list(request):
    users = User.objects.all()
    return render(request, 'usuarios.html', {'users': users})


@staff_member_required
@csrf_exempt
def user_create(request):
    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        is_staff = data.get('is_staff') == 'on'
        if User.objects.filter(username=username).exists():
            users = User.objects.all()
            error = f'Ya existe un usuario con el nombre "{username}".'
            return render(request, 'usuarios.html', {'users': users, 'error': error})
        user = User.objects.create_user(username=username, password=password)
        user.is_staff = is_staff
        user.save()
        return redirect(reverse('users_list'))
    return HttpResponseBadRequest('Método no permitido')


@staff_member_required
@csrf_exempt
def user_edit(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return HttpResponseBadRequest('Usuario no encontrado')
    if request.method == 'POST':
        data = request.POST
        user.username = data.get('username')
        if data.get('password'):
            user.set_password(data.get('password'))
        user.is_staff = data.get('is_staff') == 'on'
        user.save()
        return redirect(reverse('users_list'))
    return HttpResponseBadRequest('Método no permitido')


@staff_member_required
@csrf_exempt
def user_delete(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return HttpResponseBadRequest('Usuario no encontrado')
    if request.method == 'POST':
        user.delete()
        return redirect(reverse('users_list'))
    return HttpResponseBadRequest('Método no permitido')
