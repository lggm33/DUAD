import os
import platform
import sys

def clear_screen():
    """
    Clear the terminal screen based on the operating system
    """
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def display_calculator(current_number, message=""):
    """
    Display the calculator interface
    """
    clear_screen()
    print("\n=== CALCULADORA ===")
    print(f"Número actual: {current_number}")
    
    if message:
        print(f"\n{message}")
    
    print("\nMenú de operaciones:")
    print("1. Suma")
    print("2. Resta")
    print("3. Multiplicación")
    print("4. División")
    print("5. Borrar resultado")
    print("6. Salir")

def main():
    """
    Simple command line calculator with exception handling
    """
    current_number = 0
    message = ""
    
    while True:
        display_calculator(current_number, message)
        message = ""  # Reset message for next iteration
        
        try:
            option = int(input("\nSeleccione una opción (1-6): "))
            
            if option == 6:
                clear_screen()
                print("¡Hasta luego!")
                # Add a sys.exit() for testability
                sys.exit(0)
            
            if option == 5:
                current_number = 0
                message = "Resultado borrado."
                continue
            
            if option < 1 or option > 6:
                raise ValueError("Opción inválida. Por favor seleccione un número entre 1 y 6.")
            
            # Get the second number for the operation
            second_number = float(input("Ingrese el número para la operación: "))
            
            if option == 1:
                current_number += second_number
                message = f"Suma: {current_number - second_number} + {second_number} = {current_number}"
            elif option == 2:
                current_number -= second_number
                message = f"Resta: {current_number + second_number} - {second_number} = {current_number}"
            elif option == 3:
                old_number = current_number
                current_number *= second_number
                message = f"Multiplicación: {old_number} × {second_number} = {current_number}"
            elif option == 4:
                if second_number == 0:
                    raise ZeroDivisionError("Error: No se puede dividir por cero.")
                old_number = current_number
                current_number /= second_number
                message = f"División: {old_number} ÷ {second_number} = {current_number}"
                
        except ValueError as e:
            if "invalid literal" in str(e):
                message = "Error: Debe ingresar un número válido."
            else:
                message = str(e)
        except ZeroDivisionError as e:
            message = str(e)
        except Exception as e:
            message = f"Error inesperado: {str(e)}"

if __name__ == "__main__":
    main()
