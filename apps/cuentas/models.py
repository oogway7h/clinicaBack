from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MinLengthValidator
from django.utils import timezone
from datetime import datetime, timedelta

# Modelo de Grupo (Clínica)
class Grupo(models.Model):
    estado_opciones = [
        ('ACTIVO', 'Activo'),
        ('SUSPENDIDO', 'Suspendido'),
        ('MOROSO', 'Moroso'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    nombre = models.CharField(
        max_length=128,
        verbose_name="Nombre de la clínica"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )
    
    direccion = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="Dirección de la clínica"
    )
    
    telefono = models.CharField(
        max_length=8,
        blank=True,
        null=True,
        validators=[MinLengthValidator(8)],
        verbose_name="Teléfono"
    )
    
    correo = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo de contacto"
    )
    
    estado = models.CharField(
        max_length=20,
        choices=estado_opciones,
        default='ACTIVO',
        verbose_name="Estado del grupo"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    fecha_suspension = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de suspensión"
    )
    
    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"
    
    def tiene_pagos_pendientes(self):
        """Verifica si el grupo tiene pagos pendientes"""
        return self.pagos.filter(estado='PENDIENTE').exists()
    
    def esta_moroso(self):
        """Verifica si el grupo está moroso (pagos vencidos)"""
        return self.pagos.filter(
            estado='PENDIENTE',
            fecha_vencimiento__lt=timezone.now()
        ).exists()
    
    def actualizar_estado(self):
        """Actualiza el estado del grupo según los pagos"""
        if self.esta_moroso():
            self.estado = 'MOROSO'
        elif self.tiene_pagos_pendientes():
            self.estado = 'ACTIVO'  # Tiene pagos pendientes pero no vencidos
        else:
            self.estado = 'ACTIVO'
        self.save()
    
    class Meta:
        verbose_name = "Grupo (Clínica)"
        verbose_name_plural = "Grupos (Clínicas)"
        ordering = ['nombre']

# Modelo de Pago
class Pago(models.Model):
    tipo_pago_opciones = [
        ('MENSUAL', 'Mensual'),
        ('TRIMESTRAL', 'Trimestral'),
        ('SEMESTRAL', 'Semestral'),
        ('ANUAL', 'Anual'),
    ]
    
    estado_opciones = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('VENCIDO', 'Vencido'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='pagos',
        verbose_name="Grupo"
    )
    
    tipo_pago = models.CharField(
        max_length=20,
        choices=tipo_pago_opciones,
        default='MENSUAL',
        verbose_name="Tipo de pago"
    )
    
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto a pagar"
    )
    
    fecha_emision = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de emisión"
    )
    
    fecha_vencimiento = models.DateTimeField(
        verbose_name="Fecha de vencimiento"
    )
    
    fecha_pago = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de pago"
    )
    
    estado = models.CharField(
        max_length=20,
        choices=estado_opciones,
        default='PENDIENTE',
        verbose_name="Estado del pago"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción o notas"
    )
    
    def save(self, *args, **kwargs):
        # Auto-generar fecha de vencimiento si no se proporciona
        if not self.fecha_vencimiento:
            if self.tipo_pago == 'MENSUAL':
                self.fecha_vencimiento = timezone.now() + timedelta(days=30)
            elif self.tipo_pago == 'TRIMESTRAL':
                self.fecha_vencimiento = timezone.now() + timedelta(days=90)
            elif self.tipo_pago == 'SEMESTRAL':
                self.fecha_vencimiento = timezone.now() + timedelta(days=180)
            elif self.tipo_pago == 'ANUAL':
                self.fecha_vencimiento = timezone.now() + timedelta(days=365)
        
        super().save(*args, **kwargs)
        
        # Actualizar estado del grupo después de guardar el pago
        self.grupo.actualizar_estado()
    
    def marcar_como_pagado(self):
        """Marca el pago como pagado"""
        self.estado = 'PAGADO'
        self.fecha_pago = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Pago {self.get_tipo_pago_display()} - {self.grupo.nombre} - {self.get_estado_display()}"
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_emision']

# Modelo de Rol
class Rol(models.Model):
    tipo_rol_opciones = [
        ('paciente', 'Paciente'),
        ('medico', 'Médico'),
        ('administrador', 'Administrador'),
        ('superAdmin', 'Super Administrador'), 
    ]

    nombre = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Nombre del rol",
        choices=tipo_rol_opciones
    )

    def __str__(self):
        return self.get_nombre_display()

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ['nombre']

# Modelo de Usuario (actualizado con grupo)
class Usuario(models.Model):  
    sexo_opciones = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]

    # Agregar referencia al grupo
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='usuarios',
        verbose_name="Grupo al que pertenece",
        null=True,  # Para usuarios super admin que no pertenecen a ningún grupo específico
        blank=True
    )

    nombre = models.CharField(
        max_length=128,
        verbose_name="Nombre completo"
    )
    
    password = models.CharField(max_length=128)
    
    correo = models.EmailField(
        unique=True,
        verbose_name="Correo electrónico"
    )
    
    sexo = models.CharField(
        max_length=1, 
        choices=sexo_opciones,
        verbose_name="Género"
    )
    
    fecha_nacimiento = models.DateField(
        verbose_name="Fecha de nacimiento"
    )
    
    telefono = models.CharField(
        max_length=8,
        blank=True,
        null=True,
        validators=[MinLengthValidator(8)],
        verbose_name="Teléfono"
    )
    
    direccion = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="Dirección"
    )
    
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro"
    )
    
    estado = models.BooleanField(
        default=True,
        verbose_name="¿Está activo?"
    )
    
    ultimo_login = models.DateTimeField(
        auto_now=True,
        verbose_name="Último ingreso"
    )
    
    rol = models.ForeignKey(
        Rol, 
        on_delete=models.PROTECT,
        verbose_name="Rol del usuario",
        related_name='usuarios',
        null=True,
        blank=True
    )

    token_reset_password = models.CharField(max_length=64, null=True, blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def puede_acceder_sistema(self):
        """Verifica si el usuario puede acceder al sistema"""
        # Super admin siempre puede acceder
        if self.rol and self.rol.nombre == 'superAdmin':
            return True
        
        # Usuarios normales solo si su grupo está activo
        if self.grupo:
            return self.grupo.estado in ['ACTIVO']
        
        return False
    
    def __str__(self):
        grupo_info = f" - {self.grupo.nombre}" if self.grupo else ""
        return f"{self.nombre} ({getattr(self.rol, 'nombre', 'Sin rol')}){grupo_info}"

    class Meta:
        verbose_name = "Usuario del sistema"
        verbose_name_plural = "Usuarios del sistema"
        ordering = ['-fecha_registro']
        indexes = [
            models.Index(fields=['correo']),
            models.Index(fields=['rol', 'estado']),
            models.Index(fields=['grupo', 'estado']),
        ]

# Modelo de Bitácora (actualizado con grupo)
class Bitacora(models.Model):
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='bitacoras',
        verbose_name="Grupo",
        null=True,  # Para acciones de super admin
        blank=True
    )
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bitacoras'
    )
    
    accion = models.TextField(
        help_text="Descripción legible de la acción (ej: 'médico Pedro eliminó al paciente Juanito')"
    )
    
    ip = models.GenericIPAddressField(null=True, blank=True)
    
    objeto = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Texto corto indicando el objeto afectado (ej: 'Paciente: Juanito (id:4)')"
    )
    
    extra = models.JSONField(
        null=True,
        blank=True,
        help_text="Información adicional en JSON (opcional)"
    )
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Registro de bitácora'
        verbose_name_plural = 'Bitácoras'

    def __str__(self):
        user = self.usuario.nombre if self.usuario else "Anónimo"
        grupo_info = f" ({self.grupo.nombre})" if self.grupo else ""
        return f"{self.timestamp.isoformat()} — {user}{grupo_info} — {self.accion[:80]}"
