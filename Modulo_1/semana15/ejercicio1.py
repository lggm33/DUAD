def bubble_sort(arr):

    if not isinstance(arr, list):
        raise TypeError("Input must be a list")

    n = len(arr)
    total_iteraciones = 0
    
    for i in range(n):
        changes = False
        total_iteraciones += 1
        for j in range(0, n-i-1):
            total_iteraciones += 1
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
                changes = True
        print(f"Iteration {i+1}: {arr}")
        if not changes:
            break
    print(f"Total interactions: {total_iteraciones}")
    return arr

if __name__ == "__main__":
    print(bubble_sort([18, 20, 27, 36, 44, 15, 55, 65, 77, 91]))

