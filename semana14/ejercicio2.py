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
        

    def pop_left(self):
        if self.size == 0:
            return None
        value = self.head.value
        self.head = self.head.next
        self.size -= 1
        return value
    
    def pop_right(self):
        if self.size == 0:
            return None
        value = self.tail.value
        self.tail = self.tail.next
        self.size -= 1
        return value
    
    def print_queue(self):
        current = self.head
        while current:
            print(current.value)
            current = current.next

queue = DoubleEndedQueue()
queue.push_left(1)
queue.push_right(2)
queue.push_left(3)
queue.print_queue()
