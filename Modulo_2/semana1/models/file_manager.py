import json 
from .task import Task

class FileManager:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_json_file_tasks(self):
        """
        Read the json file and return an array of task dictionaries.
        Handles potential errors like file not found or invalid JSON format.
        """
        try:
            with open(self.file_path, "r") as file:
                data = json.load(file)
                # Validate that data is a list
                if not isinstance(data, list):
                    print(f"Warning: Data in {self.file_path} is not a list. Converting to empty list.")
                    return []
                # Verify each item is a dictionary
                for i, item in enumerate(data):
                    if not isinstance(item, dict):
                        print(f"Warning: Item at index {i} is not a dictionary. It will be skipped.")
                        data.remove(item)
                return data
        except FileNotFoundError:
            print(f"File not found: {self.file_path}. Returning empty list.")
            return []
        except json.JSONDecodeError:
            print(f"Invalid JSON format in file: {self.file_path}. Returning empty list.")
            return []
        except Exception as e:
            print(f"Unexpected error reading file {self.file_path}: {str(e)}. Returning empty list.")
            return []
        
    def add_task_to_json_file(self, task_data):
        """
        Write the tasks to the json file. Can accept either a Task object or a dictionary.
        """
        try:
            # Convert to Task object if it's a dictionary
            if isinstance(task_data, dict):
                task_obj = Task(task_data)
            else:
                task_obj = task_data
                
            # Verify the task has the correct structure using Task's is_valid method
            if not task_obj.is_valid():
                print(f"Error: Task does not have the correct structure.")
                return False   

            # Convert Task to dictionary for storage
            task = task_obj.to_dict()
                
            # Read existing tasks
            tasks = self.read_json_file_tasks()
            
            # Check if task with same ID already exists
            for existing_task in tasks:
                if existing_task["id"] == task["id"]:
                    print(f"Error: Task with ID {task['id']} already exists.")
                    return False
            
            # Add the new task
            tasks.append(task)
            
            # Write the updated tasks list back to the file
            with open(self.file_path, "w") as file:
                json.dump(tasks, file, indent=2)
                
            return True
        except Exception as e:
            print(f"Error writing to file: {e}")
            return False
    
    def delete_task_from_json_file(self, task_id):
        """
        Delete a task from the json file.
        """
        try:
            tasks = self.read_json_file_tasks()
            
            # Find the task to delete
            deleted_task = None
            for task in tasks:
                if task["id"] == task_id:
                    deleted_task = task
                    break
            
            # If task not found, return None
            if deleted_task is None:
                return False
                
            # Filter out the task to delete
            updated_tasks = [task for task in tasks if task["id"] != task_id]
            
            # Write the updated tasks back to the file
            with open(self.file_path, "w") as file:
                json.dump(updated_tasks, file, indent=2)
                
            return deleted_task
            
        except (IOError, ValueError) as e:
            # Re-raise the exception with a more descriptive message
            raise type(e)(f"Error deleting task with ID {task_id}: {str(e)}")
    """
    Update Task data in the json file.
    """
    def update_task_in_json_file(self, task_id, task_data):
        """
        Update a task in the json file.
        """
        try:
            tasks = self.read_json_file_tasks()
            for task in tasks:
                if task["id"] == task_id:
                    task.update(task_data)
                    with open(self.file_path, "w") as file:
                        json.dump(tasks, file, indent=2)
                    return task
            return False
        except Exception as e:
            print(f"Error updating task: {e}")
            return False

    def verify_task_structure(self, task_data):
        """
        Verify the task structure by using the Task class validation
        """
        # If it's already a Task object
        if isinstance(task_data, Task):
            return task_data.is_valid()
            
        # If it's a dictionary, convert to Task and validate
        try:
            task_obj = Task(task_data)
            return task_obj.is_valid()
        except Exception as e:
            print(f"Error validating task: {e}")
            return False