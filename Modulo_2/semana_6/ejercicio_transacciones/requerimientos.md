# Ejercicios de Transacciones

Para estos ejercicios debe entregar los scripts de SQL.

1. Plantee una base de datos simple con productos, usuarios y facturas. Agregue todas las columnas necesarias para realizar las tareas planteadas.
2. Construya una transacción para realizar una compra, que debe funcionar de la siguiente manera:
    1. Validar que existe stock del producto
    2. Validar que existe el usuario insertandose
    3. Crear la factura con el usuario relacionado
    4. Reducir el stock del producto
3. Construya una transacción para realizar el retorno de un producto, que funcione de la siguiente manera:
    1. Validar que la factura existe en la DB
    2. Aumentar el stock del producto en la cantidad que se compró
    3. Actualizar la factura y marcarla como retornada.