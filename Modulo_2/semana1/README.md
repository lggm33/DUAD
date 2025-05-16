# Task Management API

This is a RESTful API developed with Flask for task management. It allows creating, reading, updating, and deleting tasks (CRUD operations) through both a web interface and JSON endpoints.

## Project Structure

```
Modulo_2/semana1/
├── main.py                # Main Flask application with all routes
├── models/
│   ├── file_manager.py    # File management for reading/writing tasks to JSON file
│   └── task.py            # Data model for tasks
├── templates/             # HTML templates for web interface
│   ├── add_task.html
│   ├── delete_task.html
│   ├── index.html
│   └── update_task.html
├── example_tasks.json     # Example data format for tasks
└── api.http               # Example HTTP requests to test the API
```

## Features

- **View Tasks**: List all stored tasks
- **Add Tasks**: Interface to create new tasks
- **Update Tasks**: Modify existing tasks
- **Delete Tasks**: Remove tasks from the system

## Data Model

Each task has the following fields:
- **id**: Unique identifier (integer)
- **title**: Task title (text)
- **description**: Detailed description (text)
- **state**: Task status (options: "Por Hacer", "En Progreso", "Completada")

## Requirements

- Python 3.6 or higher
- Flask

## Installation

1. Clone the repository or download the project files

2. Install dependencies:
```bash
pip install flask
```

3. Navigate to the project directory:
```bash
cd path/to/Modulo_2/semana1
```

## Execution

1. Start the application:
```bash
python main.py
```

2. Access the web application in your browser:
```
http://localhost:5000
```

## API Endpoints

### Get all tasks
```
GET /tasks
```

### Add a task
```
POST /tasks/add
Content-Type: application/json

{
    "title": "Task name",
    "description": "Task description",
    "state": "Por Hacer"
}
```

### Update a task
```
PATCH /tasks/update/{id}
Content-Type: application/json

{
    "title": "New title",
    "description": "New description",
    "state": "En Progreso"
}
```

### Delete a task
```
DELETE /tasks/delete/{id}
```

## Testing with API.HTTP

The `api.http` file contains example requests that can be executed with extensions like REST Client in Visual Studio Code to test the API.

## Storage

Tasks are stored in a JSON file called `tasks.json` in the application's root directory. If the file doesn't exist, it will be created automatically when adding the first task. 