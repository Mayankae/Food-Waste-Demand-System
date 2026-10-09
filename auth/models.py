from database import execute_query, execute_dml

class UserModel:
    """User database access model."""

    @staticmethod
    def get_by_email(email):
        rows = execute_query("SELECT * FROM users WHERE email = ? AND is_active = 1;", [email])
        return rows[0] if rows else None

    @staticmethod
    def get_by_id(user_id):
        rows = execute_query("SELECT user_id, email, full_name, role, created_at, is_active FROM users WHERE user_id = ?;", [user_id])
        return rows[0] if rows else None

    @staticmethod
    def get_all_users():
        return execute_query("SELECT user_id, email, full_name, role, created_at, is_active FROM users ORDER BY user_id ASC;")

    @staticmethod
    def create_user(email, full_name, password_hash, role="Viewer"):
        return execute_dml(
            "INSERT INTO users (email, full_name, password_hash, role) VALUES (?, ?, ?, ?);",
            [email, full_name, password_hash, role]
        )

    @staticmethod
    def update_role(user_id, new_role):
        return execute_dml("UPDATE users SET role = ? WHERE user_id = ?;", [new_role, user_id])
