class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

class DoubleEndedQueue:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
        
    def push_left(self, value):
        new_node = Node(value)
        if self.size == 0:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head = new_node
        self.size += 1
        
    def push_right(self, value):
        new_node = Node(value)
        if self.size == 0:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        self.size += 1
        

    def pop_left(self):
        if self.size == 0:
            return None
        
        value = self.head.value
        
        if self.head == self.tail:
            self.head = None
            self.tail = None
        else:
            self.head = self.head.next
        
        self.size -= 1
        return value
    
    def pop_right(self):
        if self.head is None:  
            return None
        
        if self.head == self.tail:  
            value = self.head.value
            self.head = None
            self.tail = None
            self.size -= 1
            return value
        
        
        current = self.head
        while current.next != self.tail:
            current = current.next
        
       
        value = self.tail.value
        self.tail = current  
        self.tail.next = None 
        self.size -= 1
        return value
    
    def print_queue(self):
        current = self.head
        while current:
            print(current.value)
            current = current.next

# Example usage of all methods
print("Creating a new queue")
queue = DoubleEndedQueue()

# push_left
print("\nAdding elements to the left (front)")
queue.push_left(10)
queue.push_left(20)
queue.push_left(30)
print("Queue after pushing 30, 20, 10 to the left:")
queue.print_queue()

# push_right
print("\nAdding elements to the right (back)")
queue.push_right(40)
queue.push_right(50)
print("Queue after pushing 40, 50 to the right:")
queue.print_queue()

# pop_left
print("\nRemoving elements from the left (front)")
value = queue.pop_left()
print(f"Removed value from left: {value}")
print("Queue after pop_left:")
queue.print_queue()

# pop_right
print("\nRemoving elements from the right (back)")
value = queue.pop_right()
print(f"Removed value from right: {value}")
print("Queue after pop_right:")
queue.print_queue()

# Empty the queue
print("\nEmptying the queue")
while queue.size > 0:
    print(f"Popping left: {queue.pop_left()}")

print("\nIs queue empty?", queue.size == 0)

# Add again to show both sides work after emptying
print("\nAdding new elements after emptying")
queue.push_left(100)
queue.push_right(200)
print("Final queue:")
queue.print_queue()

