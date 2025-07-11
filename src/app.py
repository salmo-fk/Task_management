from flask import Flask, request, jsonify
from flasgger import Swagger
#import task_manager
#import user_manager
from src import task_manager
from src import user_manager


app = Flask(__name__)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/docs/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, config=swagger_config)


def parse_pagination_args():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        if page < 1:
            return None, None, jsonify(error="Page must be >= 1"), 400
        if page_size < 1:
            return None, None, jsonify(error="Page size must be >= 1"), 400
    except ValueError:
        return None, None, jsonify(error="Invalid pagination parameters. 'page' and 'page_size' must be integers."), 400
    return page, page_size, None, None


@app.route("/tasks", methods=["GET"])
def list_tasks():
    """
    Get list of tasks with optional filtering, sorting and pagination
    ---
    parameters:
      - name: filter_status
        in: query
        type: string
        enum: [TODO, ONGOING, DONE]
        required: false
        description: Filter tasks by status
      - name: sort_by
        in: query
        type: string
        enum: [created_at, title, status]
        required: false
        description: Sort tasks by this field
      - name: ascending
        in: query
        type: boolean
        required: false
        description: Sort ascending if true, descending if false (default false)
      - name: page
        in: query
        type: integer
        required: false
        description: Page number (default 1)
      - name: page_size
        in: query
        type: integer
        required: false
        description: Number of tasks per page (default 20)
    responses:
      200:
        description: List of tasks with pagination metadata
        schema:
          type: object
          properties:
            tasks:
              type: array
              items:
                type: object
            total_tasks:
              type: integer
            total_pages:
              type: integer
            current_page:
              type: integer
            page_size:
              type: integer
      400:
        description: Invalid parameters
    """
    filter_status = request.args.get("filter_status")
    sort_by = request.args.get("sort_by", "created_at")
    ascending = request.args.get("ascending", "false").lower() == "true"

    # Validate filter_status if provided
    if filter_status is not None and filter_status not in {"TODO", "ONGOING", "DONE"}:
        return jsonify(error="Invalid filter_status. Allowed values: TODO, ONGOING, DONE"), 400

    # Validate sort_by
    if sort_by not in {"created_at", "title", "status"}:
        return jsonify(error="Invalid sort_by. Allowed values: created_at, title, status"), 400

    page, page_size, error_response, status_code = parse_pagination_args()
    if error_response:
        return error_response, status_code

    # Récupération de toutes les tâches
    tasks = task_manager.get_tasks()["tasks"]


    # Filtrer par status si demandé
    if filter_status:
        tasks = [t for t in tasks if t["status"] == filter_status]
    status_order = {"TODO": 0, "ONGOING": 1, "DONE": 2}

    if sort_by == "status":
        tasks.sort(key=lambda t: status_order.get(t["status"], 99), reverse=not ascending)
    else:
        tasks.sort(key=lambda t: t[sort_by], reverse=not ascending)

    total_tasks = len(tasks)
    total_pages = (total_tasks + page_size - 1) // page_size

    if page > total_pages and total_pages != 0:
        tasks_page = []
    else:
        start = (page - 1) * page_size
        end = start + page_size
        tasks_page = tasks[start:end]

    return jsonify({
        "tasks": tasks_page,
        "total_tasks": total_tasks,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size
    })


@app.route("/tasks", methods=["POST"])
def create_task():
    """
    Create a new task
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
          properties:
            title:
              type: string
            description:
              type: string
    responses:
      201:
        description: Task created
      400:
        description: Invalid input
    """
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    try:
        task = task_manager.add_task(
            title=data.get("title", ""),
            description=data.get("description", "")
        )
        return jsonify(task), 201
    except ValueError as e:
        return jsonify(error=str(e)), 400

@app.route("/users", methods=["POST"])
def create_user():
    """
    Create a new user
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - email
          properties:
            name:
              type: string
              maxLength: 50
            email:
              type: string
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid input or duplicate email
    """
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    try:
        user = user_manager.create_user(
            name=data.get("name", ""),
            email=data.get("email", "")
        )
        return jsonify(user), 201
    except ValueError as e:
        return jsonify(error=str(e)), 400
        
@app.route("/tasks/<int:task_id>/assign", methods=["PATCH"])
def assign_task(task_id):
    """
    Assign a task to a user or unassign it
    ---
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
        description: ID of the task to assign
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: integer
              nullable: true
              description: ID of the user to assign to. Null to unassign.
    responses:
      200:
        description: Task assigned/unassigned successfully
      400:
        description: Missing or invalid input
      404:
        description: Task or user not found
    """
    data = request.get_json()
    if data is None or "user_id" not in data:
        return jsonify(error="Missing 'user_id' in request body"), 400

    user_id = data["user_id"]  # can be None (for unassigning)

    try:
        task = task_manager.assign_task(task_id, user_id)
        return jsonify(task)
    except LookupError as e:
        return jsonify(error=str(e)), 404
    except Exception as e:
        return jsonify(error=str(e)), 400

@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    """
    Get a task by ID
    ---
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Task found
      404:
        description: Task not found
    """
    try:
        return jsonify(task_manager.get_task_by_id(task_id))
    except LookupError:
        return jsonify(error="Task not found"), 404


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    """
    Update a task by ID (title and/or description)
    ---
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            description:
              type: string
    responses:
      200:
        description: Task updated
      400:
        description: Validation error
      404:
        description: Task not found
    """
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    try:
        task = task_manager.update_task(
            task_id,
            title=data.get("title"),
            description=data.get("description")
        )
        return jsonify(task)
    except LookupError:
        return jsonify(error="Task not found"), 404
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.route("/tasks/<int:task_id>/status", methods=["PATCH"])
def change_task_status(task_id):
    """
    Change status of a task
    ---
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: ["TODO", "ONGOING", "DONE"]
    responses:
      200:
        description: Status updated
      400:
        description: Invalid status
      404:
        description: Task not found
    """
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify(error="Missing 'status' field in request body"), 400

    try:
        task = task_manager.update_task_status(task_id, data["status"])
        return jsonify(task)
    except LookupError:
        return jsonify(error="Task not found"), 404
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """
    Delete a task by ID
    ---
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
    responses:
      204:
        description: Task deleted successfully (no content)
      404:
        description: Task not found
    """
    try:
        task_manager.delete_task(task_id)
        return '', 204
    except LookupError:
        return jsonify(error="Task not found"), 404


@app.route("/tasks/search", methods=["GET"])
def search():
    """
    Search tasks by keyword with pagination
    ---
    parameters:
      - name: keyword
        in: query
        type: string
        required: false
        description: Keyword to search for
      - name: page
        in: query
        type: integer
        required: false
        description: Page number (default 1)
      - name: page_size
        in: query
        type: integer
        required: false
        description: Number of tasks per page (default 20)
    responses:
      200:
        description: Search results with pagination metadata
        schema:
          type: object
          properties:
            tasks:
              type: array
              items:
                type: object
            total_tasks:
              type: integer
            total_pages:
              type: integer
            current_page:
              type: integer
            page_size:
              type: integer
    """
    keyword = request.args.get("keyword", "")
    page, page_size, error_response, status_code = parse_pagination_args()
    if error_response:
        return error_response, status_code

    tasks = task_manager.search_tasks(keyword)
    total_tasks = len(tasks)
    total_pages = (total_tasks + page_size - 1) // page_size

    if page > total_pages and total_pages != 0:
        tasks_page = []
    else:
        start = (page - 1) * page_size
        end = start + page_size
        tasks_page = tasks[start:end]

    return jsonify({
        "tasks": tasks_page,
        "total_tasks": total_tasks,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size
    })

@app.route("/users", methods=["GET"])
def list_users():
    """
    List all users with pagination (sorted by name)
    ---
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
      - name: page_size
        in: query
        type: integer
        required: false
        default: 20
    responses:
      200:
        description: List of users
        schema:
          type: object
          properties:
            users:
              type: array
              items:
                type: object
            total_users:
              type: integer
            total_pages:
              type: integer
            current_page:
              type: integer
            page_size:
              type: integer
      400:
        description: Invalid pagination
    """
    page, page_size, error_response, status_code = parse_pagination_args()
    if error_response:
        return error_response, status_code

    try:
        result = user_manager.list_users(page, page_size)
        return jsonify(result)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    
@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """
    Get user by ID
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: User found
      404:
        description: User not found
    """
    try:
        user = user_manager.get_user_by_id(user_id)
        return jsonify(user)
    except LookupError:
        return jsonify(error="User not found"), 404

if __name__ == "__main__":
    app.run(debug=True)
