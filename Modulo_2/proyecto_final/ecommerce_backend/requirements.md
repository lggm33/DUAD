# **Modulo 2: Backend - Proyecto Final 🐾**

- En este proyecto vamos a utilizar todos los conocimientos aprendidos durante la *ruta del backend* para crear un backend completo.
- Las herramientas y bibliotecas que puedes utilizar están limitadas a las que hemos visto durante las lecciones previas.
    - Sin embargo puedes utilizar cualquier información que encuentres en internet o de trabajos pasados.

## **Enunciado 📜**

- Eres un desarrollador que trabaja para un e-commerce.
- La página web vende varios tipos de productos para mascotas, pero por el momento todas las compras se manejan mediante SINPE y una hoja de Excel.
- Por esta razón, se le solicitó a usted que creara un servicio para manejar el stock y las ventas de los productos.

Para esto debe desarrollar las siguientes funcionalidades:

- Módulo de usuarios y autenticación 🔐
    - Este módulo debe encargarse de realizar todo lo relacionado con autenticación. Debe permitir operaciones como iniciar sesión y registro, y debe encargarse también de la validación de las sesiones/tokens de las solicitudes que ingresen a los demás módulos.
    - También debe ser capaz de validar los permisos de un usuario, de manera que existan roles de administrador y cliente, donde se limiten las funcionalidades de la aplicación dependiendo de su rol.
- Módulo de Productos 🏷️
    - Este módulo se encarga de registrar y administrar los productos. Debe permitir consultar los productos existentes, modificar sus datos, eliminar productos y agregar nuevos productos.
    - Los productos también deben actualizarse cuando se realicen operaciones a través del módulo de ventas.
- Módulo de Ventas 🛒
    - Este módulo se encarga de todas las operaciones relacionadas a ventas. Las funcionalidades requeridas son las siguientes:
        - Carritos: Debe ser capaz de crear carritos de compra, manejar sus productos y volver a carritos previos que no se finalizaron
        - Ventas: Debe ser capaz de convertir carritos de compra en ventas. Esto implica que debe generar una factura y modificar los productos como se necesite, reduciendo su stock en la cantidad que hayan sido comprados. Para esto también debe solicitar una dirección de facturación y datos de pago.
        - Facturas: Debe implementar también servicios para consultar una factura, que a partir del número de factura retorne los datos de la compra que se realizó. También debe ser posible realizar devoluciones, restaurando el stock de los productos.

## **Requerimientos Técnicos y de Documentación ⚙️**

- A continuación se detallan las limitaciones y especificaciones técnicas que requiere el backend.

### **Base de datos 🗃️**

- La base de datos debe ser implementada en PostgreSQL
- Antes de implementar la base de datos, debe realizar un diagrama Entidad-Relación con todas las tablas que requiera. Adicionalmente debe normalizar las tablas de ser necesario.
- Toda operación en la DB debe ser realizada a través de un ORM. No puede realizar ninguna operación directamente en la DB mediante scripts de SQL o con pgAdmin.

### **Endpoints 🌐**

- Todos las entidades relevantes de la base de datos deben tener endpoints respectivos para obtener los datos, modificarlos, eliminarlos y crear nuevos. Por ejemplo, si se crea una tabla de productos y otra de facturas, se deben tener los endpoints requeridos para administrar esos datos. Pero si se crea una tabla cruz, ésta no necesita tener endpoints.
- Los endpoints deben tener validación de permisos, de manera que cualquier endpoint que cree, elimine, o modifique productos, usuarios o facturas, solamente debe ser accesible por usuarios con el rol de administrador.
- Por otro lado, los usuarios con rol de cliente sí tienen acceso a endpoints de consulta de datos, y a los endpoints de ventas y carritos, ya que deben ser capaces de administrar sus propias compras.

### **Cacheo 🚀**

- Debe identificar cuales de los endpoints pueden beneficiarse de cacheo.
- Todo el cacheo debe tener sus respectivas condiciones de invalidación. Ejemplo: el caché de facturas debe invalidarse si se creó una factura nueva.
- De ser necesario, también debe determinar si los endpoint requieren o se beneficiarían de tener TTL.

### Unit Testing 🧪

- Debe implementar **unit testing** en el API.
- Procure cubrir el código de manera adecuada, incluyendo casos de éxito y casos de error, validando que se muestren los mensajes correspondientes de manera adecuada.
- No se trata únicamente de escribir tests para que “pasen siempre”, sino de realmente garantizar que el código maneja escenarios correctos y fallos esperados.
- Debe incluir un **script o programa que ejecute los tests automáticamente**, generando un breve reporte de resultados.
- Asegúrese de incluir instrucciones claras en la documentación de cómo correr estos tests.

### **Entregables 📦**

- Para la solución, debe entregar una breve documentación con los diagramas de la base de datos, y las justificaciones de las decisiones técnicas que haya tomado, como por ejemplo por qué le puso cacheo a un endpoint, o por qué le agregó TTL a un caché.
- Adicionalmente, debe crear un **README** con las instrucciones básicas de cómo ejecutar el servidor y la DB. Imagine que este README va a ser utilizado por otro desarrollador después de usted.
- Los **Unit Tests** deben estar incluidos en el mismo PR y listos para ser ejecutados según lo documentado.
- Finalmente, el código del servidor debe ser entregado como usualmente se hace con los ejercicios, a través de un PR en Github.