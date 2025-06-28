import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    Modelo base con campos comunes para todos los demás modelos.
    Utiliza UUID como clave primaria y añade timestamps para auditoría.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de actualización")
    deleted_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha de eliminación")

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """
        Sobrescribe el método delete para implementar un borrado suave.
        """
        self.deleted_at = timezone.now()
        self.save()


class CreditProfile(BaseModel):
    """
    Almacena las configuraciones para los diferentes tipos de perfiles de crédito.
    Estos perfiles son gestionados por el Administrador.
    """
    name = models.CharField(max_length=100, unique=True,
                            verbose_name="Nombre del Perfil")
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Tasa de Interés Nominal Mensual (%)",
        help_text="Tasa de interés mensual. Ej: 1.91 para 1.91%",
        validators=[MinValueValidator(0)]
    )
    guarantee_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Porcentaje de Afianzamiento (%)",
        help_text="Porcentaje sobre el monto solicitado para el afianzamiento.",
        validators=[MinValueValidator(0)]
    )
    guarantee_vat_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=19.00, verbose_name="IVA del Afianzamiento (%)",
        help_text="Porcentaje de IVA que se aplica sobre el valor del afianzamiento. Ej: 19.00",
        validators=[MinValueValidator(0)]
    )
    grace_period_days = models.IntegerField(
        verbose_name="Días de Interés de Carencia",
        help_text="Número de días para el cálculo del interés de carencia.",
        validators=[MinValueValidator(0)]
    )
    insurance_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Porcentaje de Seguro (%)",
        help_text="Porcentaje sobre el monto solicitado para el seguro de vida.",
        validators=[MinValueValidator(0)]
    )
    broker_commission_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Comisión del Corredor (%)",
        help_text="Porcentaje de comisión para el corredor autorizado.",
        validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Perfil de Crédito"
        verbose_name_plural = "Perfiles de Crédito"
        ordering = ['name']
