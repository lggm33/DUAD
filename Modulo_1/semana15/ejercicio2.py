def bubble_sort_reverse(arr):

    total_iteraciones = 0
    n = len(arr)

    for i in range(n):
        changes = False
        total_iteraciones += 1
        for j in range(n-1, i, -1):
            total_iteraciones += 1
            if arr[j] < arr[j-1]:
                arr[j], arr[j-1] = arr[j-1], arr[j]
                changes = True
        print(f"Iteration {i+1}: {arr}")
        if not changes:
            break
    print(f"Total de iteraciones: {total_iteraciones}")
    return arr

if __name__ == "__main__":
    print(bubble_sort_reverse([5,8,1,3,7,2]))

