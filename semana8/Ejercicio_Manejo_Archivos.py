def main():
    list_songs = []
    
    with open("canciones.txt", "r") as file:
        for line in file.readlines():
            list_songs.append(line.strip())
            print(list_songs)
    
    list_songs.sort()
    with open("canciones_ordenadas.txt", "w") as file:
        for song in list_songs:
            file.write(song + "\n")

if __name__ == "__main__":
    main()