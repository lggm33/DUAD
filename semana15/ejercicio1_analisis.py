def bubble_sort(arr):
    n = len(arr)  # O(1)
    total_iteraciones = 0  # O(1)
    
    for i in range(n):  # O(n)
        changes = False  # O(1)
        total_iteraciones += 1  # O(1)
        for j in range(0, n-i-1):  # O(n)
            total_iteraciones += 1  # O(1)
            if arr[j] > arr[j+1]:  # O(1)
                arr[j], arr[j+1] = arr[j+1], arr[j]  # O(1)
                changes = True  # O(1)
        print(f"Iteration {i+1}: {arr}")  # O(1)
        if not changes:  # O(1)
            break  # O(1)
    print(f"Total interactions: {total_iteraciones}")  # O(1)
    return arr  # O(1)

if __name__ == "__main__":
    print(bubble_sort([18, 20, 27, 36, 44, 15, 55, 65, 77, 91])) # O(n^2)

