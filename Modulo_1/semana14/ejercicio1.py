class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

class Stack:
    def __init__(self):
        self.top = None
        self.size = 0

    def push(self, value):
        new_node = Node(value)
        new_node.next = self.top
        self.top = new_node
        self.size += 1

    def pop(self):
        if self.size == 0:
            return None
        value = self.top.value
        self.top = self.top.next
        self.size -= 1
        return value
    
    def print_stack(self):
        current = self.top
        while current:
            print(current.value)
            current = current.next

stack = Stack()
stack.push(1)
stack.push(2)
stack.push(3)
stack.print_stack()
print("++++++++++++++++")
stack.pop()
stack.print_stack()
print("++++++++++++++++")
stack.pop()
stack.print_stack()
print("++++++++++++++++")
stack.pop()
stack.print_stack()




        