class BinaryTree:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
    
    def print_tree(self):
        """Print the entire binary tree structure."""
        self._print_tree_helper(self, 0)
    
    def _print_tree_helper(self, node, level):
        """Helper method to print the tree with proper indentation."""
        if node is None:
            return
        
        # Print right branch first (will appear at the top)
        self._print_tree_helper(node.right, level + 1)
        
        # Print current node with indentation
        print("    " * level + str(node.value))
        
        # Print left branch
        self._print_tree_helper(node.left, level + 1)

# Crear un árbol binario de ejemplo
root = BinaryTree(10)
root.left = BinaryTree(5)
root.right = BinaryTree(15)
root.left.left = BinaryTree(3)
root.left.right = BinaryTree(7)
root.right.left = BinaryTree(12)
root.right.right = BinaryTree(18)

# Imprimir el árbol
root.print_tree()

