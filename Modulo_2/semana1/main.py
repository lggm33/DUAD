from flask import Flask, request, render_template, redirect, url_for, jsonify
from models.file_manager import FileManager
from models.task import Task

app = Flask(__name__)

file_manager = FileManager("./tasks.json")

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/tasks", methods=["GET", "POST", "DELETE", "PATCH"])
def tasks():
    current_tasks = file_manager.read_json_file_tasks()
    
    if request.method == "GET":
        return get_tasks(current_tasks)
    elif request.method == "POST":
        # Check if request comes from a form with _method override
        form_method = request.form.get('_method', '').upper()
        if form_method == 'DELETE':
            return delete_tasks()
        elif form_method == 'PATCH':
            return update_tasks(current_tasks)
        else:
            return create_task(current_tasks)
    elif request.method == "DELETE":
        return delete_tasks()
    elif request.method == "PATCH":
        return update_tasks(current_tasks)

def get_tasks(current_tasks):
    return current_tasks

def create_task(current_tasks):

    last_task_id = current_tasks[-1]["id"] if current_tasks else 0
    new_task_id = last_task_id + 1

    # Process data from HTML form or JSON
    try:
        if request.is_json:
            # If the request has JSON content
            task_data = request.json
            if not Task.validate_task_data(task_data):
                return jsonify({"error": "Invalid task data"}), 400
        else:
            
                task_data = {
                    "title": request.form.get("title"),
                    "description": request.form.get("description"),
                    "state": request.form.get("state")
                }
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    # Assign ID to the task
    task_data["id"] = new_task_id
    
    # Save the task
    added_task = file_manager.add_task_to_json_file(task_data)

    if added_task is False:
        return jsonify({"error": "Task not added"}), 400
    
    # Redirect if from form, return message if API
    if request.is_json:
        return jsonify({"message": "Task added successfully", "task_id": new_task_id})
    else:
        return render_template('add_task.html', task_id=new_task_id)

def delete_tasks():

    try:

        if request.is_json:
            task_id = request.json.get('task_id')
            if not task_id:
                return jsonify({"error": "Task ID is required"}), 400
        else:
            task_id = request.form.get('task_id')
            if not task_id:
                return jsonify({"error": "Task ID is required"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    try:
        task_id = int(task_id)
    except (ValueError, TypeError):
        if request.is_json:
            return jsonify({"error": "Task ID must be a number"}), 400
        else:
            return render_template('delete_task.html', error="Task ID must be a number")
    
    deleted_task = file_manager.delete_task_from_json_file(task_id)

    if deleted_task is False:
        return jsonify({"error": "Task not found"}), 404
    
    if request.is_json:
        return jsonify({"message": "Task deleted successfully", "deleted_task": deleted_task})
    else:
        return render_template('delete_task.html', deleted_task=deleted_task)
        
def update_tasks(current_tasks):
    try:
        # Obtener el task_id según el tipo de request
        if request.is_json:
            return handle_api_update(current_tasks)
        else:
            return handle_form_update(current_tasks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def handle_api_update(current_tasks):

    task_id = request.json.get("task_id")
    if not task_id:
        return jsonify({"error": "Task ID is required"}), 400
        
    try:
        task_id = int(task_id)
    except ValueError:
        return jsonify({"error": "Invalid task ID format"}), 400

    task_exists = any(task["id"] == task_id for task in current_tasks)
    if not task_exists:
        return jsonify({"error": f"Task with ID {task_id} not found"}), 404
        
    current_task = next(task for task in current_tasks if task["id"] == task_id)
    
    task_data = {
        "id": task_id,
        "title": request.json.get("title", current_task["title"]),
        "description": request.json.get("description", current_task["description"]),
        "state": request.json.get("state", current_task["state"])
    }
    
    if request.json.get("state"):
        valid_states = ['Por Hacer', 'En Progreso', 'Completada']
        if task_data['state'] not in valid_states:
            return jsonify({
                "error": f"Invalid state. Must be one of: {', '.join(valid_states)}"
            }), 400

    updated_task = file_manager.update_task_in_json_file(task_id, task_data)
    
    if updated_task is False:
        return jsonify({"error": "Failed to update task"}), 500
        
    return jsonify({
        "message": "Task updated successfully",
        "updated_task": updated_task
    })

def handle_form_update(current_tasks):
    # Validar y obtener task_id
    task_id = request.form.get("task_id")
    if not task_id:
        return jsonify({"error": "Task ID is required"}), 400
        
    try:
        task_id = int(task_id)
    except ValueError:
        return jsonify({"error": "Invalid task ID format"}), 400


    task_exists = any(task["id"] == task_id for task in current_tasks)
    if not task_exists:
        return render_template('update_task.html', error=f"Task with ID {task_id} not found"), 404
        

    current_task = next(task for task in current_tasks if task["id"] == task_id)
    
    # Verificar si es un formulario vacío (primera carga)
    is_from_empty_form = {
        "title": request.form.get("title", ""),
        "description": request.form.get("description", ""),
        "state": request.form.get("state", "")
    }

    if all(value == "" for value in is_from_empty_form.values()):
        return render_template('update_task.html', 
                             task_id=task_id, 
                             title=current_task["title"], 
                             description=current_task["description"], 
                             state=current_task["state"])


    task_data = {
        "id": task_id,
        "title": request.form.get("title", current_task["title"]),
        "description": request.form.get("description", current_task["description"]),
        "state": request.form.get("state", current_task["state"])
    }

    if request.form.get("state"):
        valid_states = ['Por Hacer', 'En Progreso', 'Completada']
        if task_data['state'] not in valid_states:
            return render_template('update_task.html', 
                                 error=f"Invalid state. Must be one of: {', '.join(valid_states)}"), 400

    # Actualizar la tarea
    updated_task = file_manager.update_task_in_json_file(task_id, task_data)
    
    if updated_task is False:
        return render_template('update_task.html', error="Failed to update task"), 500
        
    return render_template('update_task.html', 
                         message="Task updated successfully",
                         updated_task=updated_task)

@app.route("/tasks/add", methods=['GET'])
def add_task_info():
    if request.method == "GET":
        return render_template('add_task.html')

@app.route("/tasks/delete", methods=["GET"])
def delete_task_info():
    # Show the general delete form (without a specific task ID)
    return render_template('delete_task.html')

    # Handle the form submission to delete a task by its ID
    task_id = request.form.get('task_id')
    if task_id:
        try:
            task_id = int(task_id)
            return redirect(url_for('delete_task', task_id=task_id))
        except ValueError:
            return render_template('delete_task.html', error="Invalid task ID format"), 400
    else:
        return render_template('delete_task.html', error="Task ID is required"), 400

@app.route("/tasks/update", methods=["GET"])
def update_task_info():
    return render_template('update_task.html')


if __name__ == "__main__":
    app.run(host="localhost", debug=True)