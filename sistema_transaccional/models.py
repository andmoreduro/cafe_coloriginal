import uuid

from django.db import models
from django.utils import timezone

def current_time():
    return timezone.localtime().time()


class Empleado(models.Model):
    id = models.TextField(primary_key=True, editable=False)
    nombre = models.TextField()
    telefono = models.JSONField()

    class Meta:
        db_table = "Empleado"
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"


class Credencial(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    correo = models.TextField()
    clave = models.TextField()
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "Credencial"
        verbose_name = "Credencial"
        verbose_name_plural = "Credenciales"


class Sesion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credencial = models.ForeignKey(Credencial, on_delete=models.CASCADE, db_column="id_crendencial")
    fecha = models.DateField(default=timezone.localdate)
    hora_inicial = models.TimeField(default=current_time)
    fecha_hora_cierre = models.DateTimeField(null=True)
    es_administrativa = models.BooleanField(default=False)
    estado = models.BooleanField(default=True)

    def es_valida(self):
        return self.estado == True or self.fecha != timezone.localdate()

    def invalidar(self):
        self.fecha_hora_cierre = timezone.now()
        self.estado = False

    class Meta:
        db_table = "Sesion"
        verbose_name = "Sesión"
        verbose_name_plural = "Sesiones"


class Permiso(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    nombre = models.TextField(unique=True, editable=False)
    descripcion = models.TextField()

    class Meta:
        db_table = "Permiso"
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"


class DetallePermiso(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, db_column="id_permiso")
    fecha_inicial = models.DateField(default=timezone.localdate)
    fecha_terminacion = models.DateField(default=None, null=True)
    fecha_final = models.DateField(default=None, null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "DetallePermiso"
        verbose_name = "Detalle de Permiso"
        verbose_name_plural = "Detalles de Permiso"


class FormaPago(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    nombre = models.TextField(unique=True, editable=False)
    comision = models.JSONField()

    class Meta:
        db_table = "FormaPago"
        verbose_name = "Forma de Pago"
        verbose_name_plural = "Formas de Pago"


class Factura(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    forma_pago = models.ForeignKey(FormaPago, on_delete=models.CASCADE, db_column="id_forma_pago")
    cedula_cliente = models.TextField()
    fecha = models.DateField(default=timezone.localdate)
    hora = models.TimeField(default=current_time)
    total = models.DecimalField(max_digits=25, decimal_places=2)
    total_IVA = models.DecimalField(max_digits=25, decimal_places=2)

    class Meta:
        db_table = "Factura"
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"


class Producto(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    nombre = models.TextField()
    descripcion = models.TextField()

    class Meta:
        db_table = "Producto"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"


class UnidadMedida(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    abreviacion = models.TextField(unique=True, editable=False)
    nombre = models.TextField(unique=True, editable=False)
    gramos_equivalentes = models.DecimalField(max_digits=25, decimal_places=5)

    class Meta:
        db_table = "UnidadMedida"
        verbose_name = "Unidad Medida"
        verbose_name_plural = "Unidades de Medida"


class DetalleFactura(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, db_column="id_factura")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column="id_producto")
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE, db_column="id_unidad_medida")
    cantidad = models.DecimalField(max_digits=25, decimal_places=5)
    subtotal = models.DecimalField(max_digits=25, decimal_places=2)
    subtotal_IVA = models.DecimalField(max_digits=25, decimal_places=2)

    class Meta:
        db_table = "DetalleFactura"
        verbose_name = "Detalle de Factura"
        verbose_name_plural = "Detalles de Factura"


class TarifaIVA(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    porcentaje = models.DecimalField(max_digits=25, decimal_places=2)
    fecha_inicial = models.DateField(default=timezone.localdate)
    fecha_final = models.DateField(null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "TarifaIVA"
        verbose_name = "Tarifa IVA"
        verbose_name_plural = "Tarifas IVA"


class PrecioVentaProducto(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column="id_producto")
    tarifa_IVA = models.ForeignKey(TarifaIVA, on_delete=models.CASCADE, db_column="id_tarifa_IVA")
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE, db_column="id_unidad_medida")
    cantidad = models.DecimalField(max_digits=25, decimal_places=5)
    precio = models.DecimalField(max_digits=25, decimal_places=2)
    fecha_inicial = models.DateField(default=timezone.localdate)
    fecha_final = models.DateField(null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "PrecioVentaProducto"
        verbose_name = "Precio de Venta de Producto"
        verbose_name_plural = "Precios de Venta de Producto"


class Local(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    nombre = models.TextField()
    ubicacion = models.JSONField()

    class Meta:
        db_table = "Local"
        verbose_name = "Local"
        verbose_name_plural = "Locales"


class DetalleLocal(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    local = models.ForeignKey(Local, on_delete=models.CASCADE, db_column="id_local")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column="id_producto")
    cantidad_en_gramos = models.DecimalField(max_digits=25, decimal_places=5)

    class Meta:
        db_table = "DetalleLocal"
        verbose_name = "Detalle de Local"
        verbose_name_plural = "Detalles de Local"


class Envio(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    local = models.ForeignKey(Local, on_delete=models.CASCADE, db_column="id_local")

    class Meta:
        db_table = "Envio"
        verbose_name = "Envío"
        verbose_name_plural = "Envios"


class DetalleEnvio(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    envio = models.ForeignKey(Envio, on_delete=models.CASCADE, db_column="id_envio")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column="id_producto")
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE, db_column="id_unidad_medida")
    cantidad = models.DecimalField(max_digits=25, decimal_places=5)

    class Meta:
        db_table = "DetalleEnvio"
        verbose_name = "Detalle de Envío"
        verbose_name_plural = "Detalles de Envio"


class Proveedor(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    nombre = models.TextField()
    descripcion = models.TextField()

    class Meta:
        db_table = "Proveedor"
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"


class Pedido(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_column="id_proveedor")
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    total = models.DecimalField(max_digits=25, decimal_places=2)
    total_IVA = models.DecimalField(max_digits=25, decimal_places=2)
    fecha_realizado = models.DateField(default=timezone.localdate)
    fecha_recibido = models.DateField(null=True)
    estado = models.TextField(default="PENDIENTE")

    class Meta:
        db_table = "Pedido"
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"


class DetallePedido(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column="id_producto")
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, db_column="id_pedido")
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE, db_column="id_unidad_medida")
    cantidad = models.DecimalField(max_digits=25, decimal_places=5)
    subtotal = models.DecimalField(max_digits=25, decimal_places=2)
    subtotal_IVA = models.DecimalField(max_digits=25, decimal_places=2)

    class Meta:
        db_table = "DetallePedido"
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedido"


class PrecioCompraProducto(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column="id_producto")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_column="id_proveedor")
    tarifa_IVA = models.ForeignKey(TarifaIVA, on_delete=models.CASCADE, db_column="id_tarifa_IVA")
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE, db_column="id_unidad_medida")
    cantidad = models.DecimalField(max_digits=25, decimal_places=5)
    precio = models.DecimalField(max_digits=25, decimal_places=2)
    fecha_inicial = models.DateField(default=timezone.localdate)
    fecha_final = models.DateField(null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "PrecioCompraProducto"
        verbose_name = "Precio de Compra de Producto"
        verbose_name_plural = "Precios de Compra de Producto"


class Cargo(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    nombre = models.TextField(unique=True, editable=False)
    descripcion = models.TextField()
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "Cargo"
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"


class Contrato(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, db_column="id_cargo")
    local = models.ForeignKey(Local, on_delete=models.CASCADE, db_column="id_local")
    fecha_inicial = models.DateField(default=timezone.localdate)
    fecha_terminacion = models.DateField(default=None, null=True)
    fecha_final = models.DateField(null=True, blank=True)
    salario = models.DecimalField(max_digits=25, decimal_places=2)
    frecuencia_pago = models.TextField()
    estado = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.empleado.nombre} - {self.cargo.nombre}"

    class Meta:
        db_table = "Contrato"
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"


class Nomina(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, db_column="id_contrato")
    fecha_pago = models.DateField()

    class Meta:
        db_table = "Nomina"
        verbose_name = "Nomina"
        verbose_name_plural = "Nominas"


class Reduccion(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    nombre = models.TextField(unique=True, editable=False)
    descripcion = models.TextField()

    class Meta:
        db_table = "Reduccion"
        verbose_name = "Reducción"
        verbose_name_plural = "Reducciones"


class DetalleReduccion(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    nomina = models.ForeignKey(Nomina, on_delete=models.CASCADE, db_column="id_nomina")
    reduccion = models.ForeignKey(Reduccion, on_delete=models.CASCADE, db_column="id_reduccion")
    total = models.DecimalField(max_digits=25, decimal_places=2)

    class Meta:
        db_table = "DetalleReduccion"
        verbose_name = "Detalle de Reducción"
        verbose_name_plural = "Detalles de Reducción"
