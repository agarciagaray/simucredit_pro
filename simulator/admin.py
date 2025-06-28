from django.contrib import admin
from .models import CreditProfile

@admin.register(CreditProfile)
class CreditProfileAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'interest_rate',
        'guarantee_percentage',
        'guarantee_vat_percentage',
        'grace_period_days',
        'insurance_percentage',
        'broker_commission_percentage',
        'created_at'
    )
    search_fields = ('name',)
    list_filter = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Tasas y Porcentajes', {
            'fields': (
                'interest_rate',
                'guarantee_percentage',
                'guarantee_vat_percentage',
                'insurance_percentage',
                'broker_commission_percentage'
            )
        }),
        ('Parámetros Adicionales', {
            'fields': ('grace_period_days',)
        }),
    )