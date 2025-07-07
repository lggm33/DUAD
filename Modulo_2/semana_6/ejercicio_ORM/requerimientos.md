## Para estos ejercicios no está permitido usar SQL, solamente se permite utilizar Python.

1. Realice el setup de SQLAlchemy, adjunte un screenshot de la validación de la versión de la biblioteca.
2. Plantee una DB con tablas para usuarios, direcciones y automóviles.
    1. Tanto las direcciones como los automóviles deben tener FKs que apunten a los usuarios.
    2. Los automoviles pueden no tener usuarios asociados, pero todas las direcciones deben tener un usuario asociado.
3. Realice un script que valide si las tablas existen, y si no las cree en el momento de su ejecución.
4. Cree una serie de clases para manejo de datos (una para usuarios, otra para automoviles y otra para direcciones) donde implemente funciones que realicen las siguientes tareas:
    1. Crear/Modificar/Eliminar un usuario nuevo.
    2. Crear/Modificar/Eliminar un automóvil nuevo.
    3. Crear/Modificar/Eliminar una dirección nueva.
    4. Asociar un automóvil a un usuario.
    5. Consultar todos los usuarios.
    6. Consultar todos los automóviles.
    7. Consultar todas las direcciones.