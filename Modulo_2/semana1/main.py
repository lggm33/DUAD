from flask import Flask, request, render_template, redirect, url_for, jsonify
from models.file_manager import FileManager
from models.task import Task

app = Flask(__name__)

file_manager = FileManager("./tasks.json")

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/tasks")
def tasks():
    tasks = file_manager.read_json_file_tasks()
    return tasks

@app.route("/tasks/add", methods=["POST", "GET"])
def add_task():
    if request.method == "GET":
        return render_template('add_task.html')
    
    elif request.method == "POST":
        current_tasks = file_manager.read_json_file_tasks()
        last_task_id = current_tasks[-1]["id"] if current_tasks else 0
        new_task_id = last_task_id + 1

        # Process data from HTML form or JSON
        if request.is_json:
            # If the request has JSON content
            task_data = request.json
            if not Task.validate_task_data(task_data):
                return jsonify({"error": "Invalid task data"}), 400
        else:
            try:
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
            return {"message": "Task added successfully", "task_id": new_task_id}
        else:
            return render_template('add_task.html')
    else:
        return "Invalid request method"

@app.route("/tasks/delete/<int:task_id>", methods=["GET", "POST", "DELETE"])
def delete_task(task_id):
    try:
        # If it's a GET request, show the delete confirmation page
        if request.method == "GET":
            return render_template('delete_task.html', task_id=task_id)
            
        # Handle DELETE requests from API or POST with _method=DELETE from form
        elif request.method == "DELETE" or (request.method == "POST" and request.form.get('_method') == 'DELETE'):
            deleted_task = file_manager.delete_task_from_json_file(task_id)
            
            if deleted_task is False:
                if request.method == "DELETE":
                    return jsonify({"error": f"Task with ID {task_id} not found"}), 404
                else:
                    # For form submissions
                    return render_template('delete_task.html', error=f"Task with ID {task_id} not found"), 404
            
            # Return different responses based on request type
            if request.method == "DELETE":
                return jsonify({
                    "message": f"Task with ID {task_id} deleted successfully",
                    "deleted_task": deleted_task
                })
            else:
                # For form submissions, redirect to tasks page
                return redirect(url_for('tasks'))
                
    except Exception as e:
        if request.method == "DELETE":
            return jsonify({"error": str(e)}), 500
        else:
            return render_template('delete_task.html', error=str(e)), 500

@app.route("/tasks/delete", methods=["GET"])
def delete_task_form():
    # Show the general delete form (without a specific task ID)
    return render_template('delete_task.html')

@app.route("/tasks/delete_by_id", methods=["POST"])
def delete_task_by_id():
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

@app.route("/tasks/update/<int:task_id>", methods=["GET", "PATCH", "POST"])
def update_task(task_id):
    try:
        tasks = file_manager.read_json_file_tasks()
        task_data = {}

        task = False
        for t in tasks:
            if t["id"] == task_id:
                task = t
                break

        if task is False:
            return render_template('update_task.html', error="Task not found"), 404
        
        if request.method == "GET":
            return render_template('update_task.html', task_id=task_id, title=task["title"], description=task["description"], state=task["state"])
        
        if request.method == "POST" and request.form.get('_method') == 'PATCH':
            
            try:
                task_data = {
                        "title": request.form.get("title"),
                        "description": request.form.get("description"),
                        "state": request.form.get("state")}
                
                updated_task = file_manager.update_task_in_json_file(task_id, task_data)

                if updated_task is False:
                    return render_template('update_task.html', error="Task not found"), 404
                
                return redirect(url_for('tasks'))
            
            except Exception as e:
                return render_template('update_task.html', error=str(e)), 500
            

        if request.method == "PATCH":
                
                try:
                    task_data = request.json

                    updated_task = file_manager.update_task_in_json_file(task_id, task_data)

                    if updated_task is False:
                        return jsonify({"error": "Task not found"}), 404    
                    
                    return jsonify({"message": "Task updated successfully", "updated_task": updated_task})
                except Exception as e:
                    return jsonify({"error": str(e)}), 500

        
        
        

        if updated_task is False:
                return render_template('update_task.html', error="Task not found"), 404
        
        return redirect(url_for('tasks'))


    except Exception as e:
        return render_template('update_task.html', error=str(e)), 500

@app.route("/tasks/update", methods=["GET"])
def update_task_form():
    return render_template('update_task.html')

@app.route("/tasks/update_by_id", methods=["POST"])
def update_task_by_id():
    task_id = request.form.get('task_id')
    if task_id:
        try:
            task_id = int(task_id)
            return redirect(url_for('update_task', task_id=task_id))
        except ValueError:
            return render_template('update_task.html', error="Invalid task ID format"), 400
    else:
        return render_template('update_task.html', error="Task ID is required"), 400

if __name__ == "__main__":
    app.run(host="localhost", debug=True)