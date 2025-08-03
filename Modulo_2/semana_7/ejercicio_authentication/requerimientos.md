# Ejercicio de Authorization

- Para este ejercicio nos vamos a basar en la solución del ejercicio guiado, por lo que es requerido que ya hayas terminado esa lección.
- Puedes copiar cualquier código que hayamos visto en clase, o utilizado en las guías.
- Todo el manejo de la DB debe ser mediante ORM, no se permite utilizar scripts directos en SQL.

## Planteo

- Recientemente fuiste incluido en un equipo de desarrollo backend, y entraste a trabajar en un proyecto ya comenzado.
- Tu equipo había finalizado la implementación del sistema de manejo de usuarios, pero el cliente necesita que comiencen con el punto principal del producto, que es una venta de frutas.
- Para la venta de frutas, necesitamos que se implementen las tablas requeridas para almacenar la información de los productos, la cual es:
    - Nombre
    - Precio
    - Fecha de entrada
    - Cantidad
- También, se requiere implementar todos los endpoints para un CRUD, donde se manejen los datos de los productos.
- Sin embargo, el cliente también necesita un servicio para realizar la venta de los productos, que al comprar un producto, se genere una factura y se guarde en la DB. Por lo que también se requiere un endpoint para consultar las facturas de un solo cliente.
- Por esta razón, el cliente requiere que existan dos tipos de usuarios:
    - Administrador: Tiene acceso a todos los endpoints del sistema
    - Usuario: Solamente tiene acceso a los endpoints de auth (login, me), al de compra de productos, y al listado de facturas.

## Solución

- Para la solución debe entregar los archivos utilizados en el ejercicio guiado, con las modificaciones necesarias, y todos los nuevos archivos que se crearon para implementar la solución que se require.
- Para la autenticación debe realizar las modificaciones necesarias para que los tokens sean generados utilizando el algoritmo **RS256.**
- Asegurese de probar sus endpoints mediante Postman, Insomnia o cURL, para verificar que funcionen adecuadamente.
- Para cualquier error del sistema, ya sea interno, o de autenticación, se espera que el servidor retorne los códigos adecuados para cada caso donde pueda fallar. Recuerde consultar la [referencia de los códigos HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) para aclarar cuando se deben usar.