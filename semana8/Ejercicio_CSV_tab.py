import csv

def main():
    
    print("Welcome to the video games CSV file generator program")
    print("Please follow the instructions")

    games_list = []

    while True:
        name = input("Enter the name of the video game: ")
        genre = input("Enter the genre of the video game: ")
        developer = input("Enter the developer of the video game: ")
        rating = input("Enter the rating of the video game: ")
        games_list.append([name, genre, developer, rating])
        continue_adding = input("Do you want to add another video game? (no to create the file/ any key to continue): ")
        if continue_adding == "no":
            break
        
    with open("video_games.csv", "w", newline="") as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(["Name", "Genre", "Developer", "Rating"])
        for game in games_list:
            writer.writerow(game)

    print("CSV file successfully generated")


if __name__ == "__main__":
    main()