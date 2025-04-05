import json

def main():
    
    print("Welcome to the Pokemon Management Program")
    print("Loading current Pokemons...")


    with open("pokemons.json", "r") as file:
         pokemons_json = json.load(file)

    print("Current Pokemons:")
    print(json.dumps(pokemons_json, indent=2, ensure_ascii=False))

    while True:
        continue_option = input("Do you want to add a pokemon? (y/n): ")
        if continue_option == "n":
            
            break
        if continue_option == "y":
            name = input("Enter the pokemon name: ")
            type_input = input("Enter the pokemon type: ")
            print("Enter the pokemon base stats: ")
            hp = input("HP: ")
            attack = input("Attack: ")
            defense = input("Defense: ")
            sp_attack = input("Sp. Attack: ")
            sp_defense = input("Sp. Defense: ")
            speed = input("Speed: ")
            pokemons_json.append({"name": {"english": name}, "type": [type_input], "base": {"HP": hp, "Attack": attack, "Defense": defense, "Sp. Attack": sp_attack, "Sp. Defense": sp_defense, "Speed": speed}})

            print("Pokemon added successfully")

        else:
            print("Invalid option")
      

    with open("pokemons.json", "w") as file:
        json.dump(pokemons_json, file, indent=2, ensure_ascii=False)
        print("Pokemons updated successfully")

    print("Goodbye!")

if __name__ == "__main__":
    main()