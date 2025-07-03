# Planteo

- Usted es el lead backend developer de una empresa de alquiler de autos. La empresa acaba de crearse, por lo que actualmente está construyendo todo el sistema desde cero.
- Su cliente le solicita una serie de requerimientos para el negocio, ya que el frontend developer está por iniciar el desarrollo de la página web, y necesita preparar el servidor para consumir los datos.
- Debe entregar todos los scripts y código que sea utilizado para completar las tareas.

## Tarea 1: Crear y popular la DB

1. Cree un nuevo schema llamado `lyfter_car_rental`. Sobre este schema serán trabajados todos los siguientes ejercicios, incluyendo los de Python.
2. Cree un script donde se cree una tabla de usuarios.
    1. Una de las columnas debe ser un ID único **autoincremental**.
    2. Esta tabla necesita ser capaz de almacenar el nombre del usuario, su correo, su username y password, así como su fecha de nacimiento y el estado de su cuenta.
    3. Adicionalmente, el script debe popular la tabla con al menos 50 usuarios nuevos. **El script debe funcionar con una única ejecución, o sea que la tabla debe crearse y seguidamente debe popularse.**
    
    <aside>
    <img src="/icons/light-bulb_yellow.svg" alt="/icons/light-bulb_yellow.svg" width="40px" />
    
    En muchos casos vamos a tener que generar datos falsos para hacer pruebas. Acá algunas páginas que te pueden ayudar:
    
    - https://www.mockaroo.com/
    - https://generatedata.com/
    - https://www.rndgen.com/data-generator
    </aside>
    
3. Cree un script igual al anterior, pero para una tabla de automoviles.
    1. Esta tabla requiere además del ID, columnas para marca, modelo, año de fabricación y estado del automovil.
4. Finalmente, cree una tabla cruz para relacionar los alquileres de los carros con los usuarios.
    1. Esta tabla requiere además de la relación, datos adicionales como fecha de alquiler y estado del alquiler. La fecha debe ser autogenerada al ingresar la nueva fila.

## Tarea 2: Pruebas básicas de la DB

1. Con la DB creada, cree los siguientes scripts:
    1. Un script que agregue un usuario nuevo
    2. Un script que agregue un automovil nuevo
    3. Un script que cambie el estado de un usuario
    4. Un script que cambie el estado de un automovil
    5. Un script que genere un alquiler nuevo con los datos de un usuario y un automovil
    6. Un script que confirme la devolución del auto al completar el alquiler, colocando el auto como disponible y completando el estado del alquiler
    7. Un script que deshabilite un automovil del alquiler
    8. Un script que obtenga todos los automoviles alquilados, y otro que obtenga todos los disponibles.

## Tarea 3: Creación del API

1. Con los scripts anteriores, cree un API que sea capaz de realizar las siguientes tareas:
    1. Creacion:
        1. Crear un usuario nuevo
        2. Crear un automovil nuevo
        3. Crear un alquiler nuevo
    2. Modificación
        1. Cambiar el estado de un automovil
        2. Cambiar el estado de un usuario
        3. Completar un alquiler
        4. Cambiar el estado de un alquiler
        5. Flagear un usuario como moroso
    3. Listado
        1. Listar todos los usuarios
        2. Listar todos los automoviles
        3. Listar todos los alquileres
        4. Nota: Todos los endpoints de listado deben ser capaces de aceptar filtros. Por ejemplo:
            1. El listado de usuarios debe ser capaz de filtrar por username
            2. El listado de autos debe ser capaz de filtrar por modelo
            3. El listado de alquileres debe ser capaz de filtrar por estado
            
            Estos son solo ejemplos, y los endpoints deben soportar filtros por cualquier columna de la tabla que consulten.