import os
import ssl
import pymysql
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_db_connection():
    context = ssl.create_default_context(
        cafile=os.environ["DB_SSL_CA"]
    )
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED

    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        connect_timeout=5,
        ssl=context,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "application": "AWS Cloud DevOps Capstone API"
    }), 200


@app.route("/api", methods=["GET"])
def home():
    return jsonify({
        "message": "Welcome to the AWS Cloud DevOps Capstone API",
        "services": [
            "Amazon EC2",
            "Amazon RDS",
            "Amazon Cognito",
            "Docker",
            "GitHub Actions",
            "Amazon CloudWatch"
        ]
    }), 200


@app.route("/api/db-check", methods=["GET"])
def db_check():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT DATABASE() AS database_name, VERSION() AS mysql_version"
            )
            result = cursor.fetchone()

        return jsonify({
            "status": "connected",
            "database": result["database_name"],
            "mysql_version": result["mysql_version"]
        }), 200

    except Exception:
        app.logger.exception("Database connection failed")
        return jsonify({
            "status": "unavailable",
            "message": "Database connection failed"
        }), 503

    finally:
        if connection:
            connection.close()


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, created_at FROM tasks ORDER BY id DESC"
            )
            tasks = cursor.fetchall()

        return jsonify({"tasks": tasks}), 200

    except Exception:
        app.logger.exception("Could not retrieve tasks")
        return jsonify({"message": "Could not retrieve tasks"}), 500

    finally:
        if connection:
            connection.close()


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True) or {}
    title = data.get("title")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"message": "A non-empty title is required"}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tasks (title) VALUES (%s)",
                (title.strip(),)
            )
            task_id = cursor.lastrowid

        return jsonify({
            "message": "Task created successfully",
            "id": task_id,
            "title": title.strip()
        }), 201

    except Exception:
        app.logger.exception("Could not create task")
        return jsonify({"message": "Could not create task"}), 500

    finally:
        if connection:
            connection.close()


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    title = data.get("title")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"message": "A non-empty title is required"}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE tasks SET title = %s WHERE id = %s",
                (title.strip(), task_id)
            )
            updated = cursor.rowcount

        if updated == 0:
            return jsonify({"message": "Task not found"}), 404

        return jsonify({
            "message": "Task updated successfully",
            "id": task_id,
            "title": title.strip()
        }), 200

    except Exception:
        app.logger.exception("Could not update task")
        return jsonify({"message": "Could not update task"}), 500

    finally:
        if connection:
            connection.close()


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM tasks WHERE id = %s",
                (task_id,)
            )
            deleted = cursor.rowcount

        if deleted == 0:
            return jsonify({"message": "Task not found"}), 404

        return jsonify({
            "message": "Task deleted successfully",
            "id": task_id
        }), 200

    except Exception:
        app.logger.exception("Could not delete task")
        return jsonify({"message": "Could not delete task"}), 500

    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
