class Task:
  def __init__(self, data: dict):
    self.id = data.get("id")
    self.title = data.get("title")
    self.description = data.get("description")
    self.state = data.get("state")

  def __str__(self):
    return f"Task(id={self.id}, title={self.title}, description={self.description}, state={self.state})"
  

  def to_dict(self):
    return {
      "id": self.id,
      "title": self.title,
      "description": self.description,
      "state": self.state}
  
  @staticmethod
  def validate_task_data(data: dict):
    """
    Static method to validate task data structure before creating a Task instance
    
    Args:
        data: Dictionary containing task data
        
    Returns:
        bool: True if data is valid, False otherwise
    """
    # Check if all required fields are present
    required_fields = ["id", "title", "description", "state"]
    if not all(field in data for field in required_fields):
      return False
      
    # Validate data types
    if not isinstance(data["id"], int):
      return False
    if not isinstance(data["title"], str):
      return False
    if not isinstance(data["description"], str):
      return False
    if not isinstance(data["state"], str):
      return False
    
    # Validate state has one of the allowed values
    allowed_states = ["Por Hacer", "En Progreso", "Completada"]
    if data["state"] not in allowed_states:
      return False
      
    return True
  
  def is_valid(self):
    """
    Verify the task structure
    """
    if not all(hasattr(self, attr) for attr in ["id", "title", "description", "state"]):
        return False
    if not isinstance(self.id, int):
      return False
    if not isinstance(self.title, str):
      return False
    if not isinstance(self.description, str):
      return False
    if not isinstance(self.state, str):
      return False
    
    # Validate state has one of the allowed values
    allowed_states = ["Por Hacer", "En Progreso", "Completada"]
    if self.state not in allowed_states:
      print(f"Error: Task state must be one of: {allowed_states}")
      return False
      
    return True
  
 