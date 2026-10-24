from decimal import Decimal

from app.errors import ReglaNegocioError
from app.models import (ActividadObra, CorteObra, DetalleCorteObra, EstadoCorte,
                        FacturaObra, PagoObra)

# Un corte "ocupa" cantidad mientras esté activo (no borrado) y no rechazado.
ESTADOS_ACTIVOS = {EstadoCorte.BORRADOR, EstadoCorte.PRESENTADO, EstadoCorte.APROBADO}
TRANSICIONES = {
    EstadoCorte.BORRADOR: {EstadoCorte.PRESENTADO},
    EstadoCorte.PRESENTADO: {EstadoCorte.APROBADO, EstadoCorte.RECHAZADO},
    EstadoCorte.APROBADO: set(),
    EstadoCorte.RECHAZADO: set(),  # un rechazado NO se cobra; se crea un corte nuevo
}
CERO = Decimal("0")


class ObraService:
    """Reglas del negocio. Recibe los repositorios CSV ya creados."""

    def __init__(self, contratos, actividades, cortes, detalles, facturas, pagos):
        self.facturas = facturas
        self.pagos = pagos
        self.contratos = contratos
        self.actividades = actividades
        self.cortes = cortes
        self.detalles = detalles

    # ---------- cálculos ----------
    def _cantidad_en_cortes(self, actividad_id: int, estados: set) -> Decimal:
        vigentes = {c.id: c.estado for c in self.cortes.listar() if c.activo}
        return sum((d.cantidad for d in self.detalles.listar()
                    if d.actividad_id == actividad_id and vigentes.get(d.corte_id) in estados), CERO)

    def cantidades_actividad(self, actividad_id: int) -> dict:
        a = self.actividades.obtener(actividad_id)
        en_activos = self._cantidad_en_cortes(actividad_id, ESTADOS_ACTIVOS)
        return {
            "contratada": a.cantidad_contratada,
            "ejecutada": a.cantidad_ejecutada,
            "en_cortes_activos": en_activos,
            "aprobada": self._cantidad_en_cortes(actividad_id, {EstadoCorte.APROBADO}),
            "disponible_para_cobrar": a.cantidad_ejecutada - en_activos,
            "pendiente_ejecutar": a.cantidad_contratada - a.cantidad_ejecutada,
        }

    def resumen_contrato(self, contrato_id: int) -> dict:
        """Separa: contratado, ejecutado, en cortes, aprobado, facturado, pagado y saldo por recaudar."""
        self.contratos.obtener(contrato_id)
        r = {k: CERO for k in ("valor_contratado", "valor_ejecutado", "valor_en_cortes_activos",
                               "valor_aprobado", "valor_disponible_para_cobrar", "valor_pendiente_ejecutar")}
        facturas_ok = {f.id: f for f in self.facturas.listar() if f.contrato_id == contrato_id and f.activo}
        for a in (x for x in self.actividades.listar() if x.contrato_id == contrato_id and x.activo):
            q, p = self.cantidades_actividad(a.id), a.precio_unitario
            r["valor_contratado"] += q["contratada"] * p
            r["valor_ejecutado"] += q["ejecutada"] * p
            r["valor_en_cortes_activos"] += q["en_cortes_activos"] * p
            r["valor_aprobado"] += q["aprobada"] * p
            r["valor_disponible_para_cobrar"] += q["disponible_para_cobrar"] * p
            r["valor_pendiente_ejecutar"] += q["pendiente_ejecutar"] * p
        r["valor_facturado"] = sum((f.valor for f in facturas_ok.values()), CERO)
        r["valor_pagado"] = sum((p.valor for p in self.pagos.listar()
                                 if p.activo and p.factura_id in facturas_ok), CERO)
        r["saldo_pendiente_recaudo"] = r["valor_facturado"] - r["valor_pagado"]
        r["valor_aprobado_sin_facturar"] = r["valor_aprobado"] - r["valor_facturado"]
        return r

    def detalles_de_corte(self, corte_id: int) -> list[DetalleCorteObra]:
        return [d for d in self.detalles.listar() if d.corte_id == corte_id]

    def valor_corte(self, corte_id: int) -> Decimal:
        return sum((d.valor for d in self.detalles_de_corte(corte_id)), CERO)

    # ---------- contratos ----------
    def eliminar_contrato(self, contrato_id: int) -> None:
        contrato = self.contratos.obtener(contrato_id)
        if any(c.contrato_id == contrato_id and c.activo and c.estado != EstadoCorte.RECHAZADO
               for c in self.cortes.listar()):
            raise ReglaNegocioError("No se puede eliminar un contrato con cortes vigentes")
        self.contratos.actualizar(contrato_id, contrato.model_copy(update={"activo": False}))

    # ---------- actividades ----------
    def _validar_actividad(self, act: ActividadObra, excluir_id=None) -> None:
        contrato = self.contratos.obtener(act.contrato_id)  # 404 si no existe
        if not contrato.activo:
            raise ReglaNegocioError("El contrato está inactivo")
        total = sum((a.valor_contratado for a in self.actividades.listar()
                     if a.contrato_id == act.contrato_id and a.activo and a.id != excluir_id), CERO)
        if total + act.valor_contratado > contrato.valor_contrato:
            raise ReglaNegocioError("Las actividades superan el valor del contrato, verifica")

    def crear_actividad(self, act: ActividadObra) -> ActividadObra:
        self._validar_actividad(act)
        return self.actividades.crear(act)

    def actualizar_actividad(self, actividad_id: int, act: ActividadObra) -> ActividadObra:
        self.actividades.obtener(actividad_id)
        self._validar_actividad(act, excluir_id=actividad_id)
        en_cortes = self._cantidad_en_cortes(actividad_id, ESTADOS_ACTIVOS)
        if act.cantidad_ejecutada < en_cortes:
            raise ReglaNegocioError(f"La ejecutada no puede ser menor a lo ya incluido en cortes ({en_cortes})")
        return self.actividades.actualizar(actividad_id, act)

    def registrar_avance(self, actividad_id: int, cantidad_ejecutada: Decimal) -> ActividadObra:
        act = self.actividades.obtener(actividad_id)
        if cantidad_ejecutada > act.cantidad_contratada:
            raise ReglaNegocioError("La cantidad ejecutada no puede superar la contratada")
        en_cortes = self._cantidad_en_cortes(actividad_id, ESTADOS_ACTIVOS)
        if cantidad_ejecutada < en_cortes:
            raise ReglaNegocioError(f"No se puede ejecutar menos de lo ya incluido en cortes ({en_cortes})")
        return self.actividades.actualizar(
            actividad_id, act.model_copy(update={"cantidad_ejecutada": cantidad_ejecutada}))

    def eliminar_actividad(self, actividad_id: int) -> None:
        act = self.actividades.obtener(actividad_id)
        if act.cantidad_ejecutada > 0:
            raise ReglaNegocioError("No se puede eliminar una actividad con avance ejecutado")
        self.actividades.actualizar(actividad_id, act.model_copy(update={"activo": False}))

    # ---------- cortes ----------
    def crear_corte(self, corte: CorteObra, items: list[tuple[int, Decimal]]) -> CorteObra:
        """items = [(actividad_id, cantidad)]. El corte nace en borrador."""
        contrato = self.contratos.obtener(corte.contrato_id)
        if not contrato.activo:
            raise ReglaNegocioError("El contrato está inactivo")
        if corte.estado != EstadoCorte.BORRADOR:
            raise ReglaNegocioError("Todo corte se crea en estado borrador")
        if not items:
            raise ReglaNegocioError("Un corte debe incluir al menos una actividad")
        ids = [i for i, _ in items]
        if len(ids) != len(set(ids)):
            raise ReglaNegocioError("Actividad repetida en el mismo corte")
        if any(c.activo and c.contrato_id == corte.contrato_id and c.numero_corte == corte.numero_corte
               for c in self.cortes.listar()):
            raise ReglaNegocioError(f"Ya existe el corte {corte.numero_corte} en este contrato")
        validados = []
        for act_id, cantidad in items:
            act = self.actividades.obtener(act_id)
            if act.contrato_id != corte.contrato_id or not act.activo:
                raise ReglaNegocioError(f"La actividad {act_id} no es válida para el contrato {corte.contrato_id}")
            if cantidad <= 0:
                raise ReglaNegocioError("La cantidad debe ser mayor que cero")
            disp = self.cantidades_actividad(act_id)["disponible_para_cobrar"]
            if cantidad > disp:
                raise ReglaNegocioError(
                    f"Actividad {act_id}: se pide {cantidad} pero solo hay {disp} disponible para cobrar")
            validados.append((act, cantidad))
        creado = self.cortes.crear(corte)
        try:
            for act, cantidad in validados:
                self.detalles.crear(DetalleCorteObra(corte_id=creado.id, actividad_id=act.id,
                                                     cantidad=cantidad, precio_unitario=act.precio_unitario))
        except Exception:  # CSV no tiene transacciones: deshacemos a mano
            for d in self.detalles_de_corte(creado.id):
                self.detalles.eliminar(d.id)
            self.cortes.eliminar(creado.id)
            raise
        return creado

    def actualizar_corte(self, corte_id: int, corte: CorteObra) -> CorteObra:
        actual = self.cortes.obtener(corte_id)
        if actual.estado != EstadoCorte.BORRADOR:
            raise ReglaNegocioError("Solo se puede editar un corte en borrador")
        return self.cortes.actualizar(
            corte_id, corte.model_copy(update={"estado": actual.estado, "contrato_id": actual.contrato_id}))

    def cambiar_estado_corte(self, corte_id: int, nuevo: EstadoCorte) -> CorteObra:
        corte = self.cortes.obtener(corte_id)
        if not corte.activo:
            raise ReglaNegocioError("El corte está inactivo")
        if nuevo not in TRANSICIONES[corte.estado]:
            raise ReglaNegocioError(f"Transición no permitida: {corte.estado.value} -> {nuevo.value}")
        return self.cortes.actualizar(corte_id, corte.model_copy(update={"estado": nuevo}))

    def eliminar_corte(self, corte_id: int) -> None:
        """Borrado lógico: el corte y sus detalles quedan como histórico, pero liberan la cantidad."""
        corte = self.cortes.obtener(corte_id)
        if corte.estado != EstadoCorte.BORRADOR:
            raise ReglaNegocioError("Solo se puede eliminar un corte en borrador")
        self.cortes.actualizar(corte_id, corte.model_copy(update={"activo": False}))


    # ---------- facturas ----------
    def valor_pagado_factura(self, factura_id: int) -> Decimal:
        return sum((p.valor for p in self.pagos.listar() if p.factura_id == factura_id and p.activo), CERO)

    def _validar_factura(self, f: FacturaObra, excluir_id=None) -> None:
        corte = self.cortes.obtener(f.corte_id)  # 404 si no existe
        self.contratos.obtener(f.contrato_id)
        if not corte.activo or corte.contrato_id != f.contrato_id:
            raise ReglaNegocioError("El corte no está activo o no pertenece a ese contrato")
        if corte.estado != EstadoCorte.APROBADO:
            raise ReglaNegocioError("Solo se factura un corte aprobado")
        activas = [x for x in self.facturas.listar() if x.activo and x.id != excluir_id]
        if any(x.numero_factura == f.numero_factura for x in activas):
            raise ReglaNegocioError(f"Ya existe la factura {f.numero_factura}")
        ya_facturado = sum((x.valor for x in activas if x.corte_id == f.corte_id), CERO)
        if ya_facturado + f.valor > self.valor_corte(f.corte_id):
            raise ReglaNegocioError(
                f"Se facturaría {ya_facturado + f.valor} y el corte vale {self.valor_corte(f.corte_id)}")

    def crear_factura(self, f: FacturaObra) -> FacturaObra:
        self._validar_factura(f)
        return self.facturas.crear(f)

    def actualizar_factura(self, factura_id: int, f: FacturaObra) -> FacturaObra:
        self.facturas.obtener(factura_id)
        if self.valor_pagado_factura(factura_id) > 0:
            raise ReglaNegocioError("No se puede editar una factura que ya tiene pagos")
        self._validar_factura(f, excluir_id=factura_id)
        return self.facturas.actualizar(factura_id, f)

    def eliminar_factura(self, factura_id: int) -> None:
        f = self.facturas.obtener(factura_id)
        if self.valor_pagado_factura(factura_id) > 0:
            raise ReglaNegocioError("No se puede eliminar una factura con pagos registrados")
        self.facturas.actualizar(factura_id, f.model_copy(update={"activo": False}))

    # ---------- pagos ----------
    def _validar_pago(self, p: PagoObra, excluir_id=None) -> None:
        f = self.facturas.obtener(p.factura_id)  # 404 si no existe
        if not f.activo:
            raise ReglaNegocioError("La factura está inactiva")
        if p.fecha_pago < f.fecha_factura:
            raise ReglaNegocioError("El pago no puede ser anterior a la fecha de la factura")
        pagado = sum((x.valor for x in self.pagos.listar()
                      if x.activo and x.factura_id == p.factura_id and x.id != excluir_id), CERO)
        if pagado + p.valor > f.valor:
            raise ReglaNegocioError(f"El pago supera el saldo de la factura (saldo {f.valor - pagado})")

    def crear_pago(self, p: PagoObra) -> PagoObra:
        self._validar_pago(p)
        return self.pagos.crear(p)

    def actualizar_pago(self, pago_id: int, p: PagoObra) -> PagoObra:
        self.pagos.obtener(pago_id)
        self._validar_pago(p, excluir_id=pago_id)
        return self.pagos.actualizar(pago_id, p)

    def eliminar_pago(self, pago_id: int) -> None:
        p = self.pagos.obtener(pago_id)
        self.pagos.actualizar(pago_id, p.model_copy(update={"activo": False}))