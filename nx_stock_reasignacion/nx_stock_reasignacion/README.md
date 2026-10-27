# Nimax - Reasignacion de piezas entre pedidos

Modulo para Odoo 19 que permite mover una cantidad reservada de un pedido de venta a otro pedido confirmado que tenga el mismo producto pendiente.

## Uso

1. Abra el pedido que actualmente tiene piezas reservadas.
2. Pulse **Reasignar piezas**.
3. Seleccione el movimiento/producto origen.
4. Seleccione el pedido y movimiento destino.
5. Indique la cantidad y pulse **Reasignar**.

## Controles

- Solo administradores de inventario.
- Mismo producto, unidad de medida, almacen y ubicacion origen.
- Ambos movimientos deben estar pendientes.
- No acepta operaciones ya recogidas.
- No permite superar lo reservado en origen ni lo pendiente en destino.
- Registra la operacion en el chatter de ambos pedidos.

## Importante

Probar primero en staging con copias de pedidos reales. La reserva usa los metodos estandar de Odoo (`_do_unreserve` y `_action_assign`).
