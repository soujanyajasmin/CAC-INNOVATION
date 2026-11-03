import sqlite3
import os
from app.core.security import get_password_hash

def reset_database():
    db_path = "cac_innovations.db"
    if not os.path.exists(db_path):
        print("Database file does not exist. Initializing fresh...")
        from app.database.init_db import init_database
        init_database()
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Disable foreign keys temporarily for truncation
    cursor.execute("PRAGMA foreign_keys = OFF;")

    tables_to_clear = [
        "tasks",
        "task_comments",
        "milestones",
        "projects",
        "project_documents",
        "invoices",
        "support_tickets",
        "notifications",
        "enquiries",
        "clients",
        "intern_submissions",
        "intern_tasks",
        "intern_batches",
        "conversation_messages",
        "ai_usage_logs",
        "audit_logs"
    ]

    for table in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table};")
            print(f"Cleared table: {table}")
        except sqlite3.OperationalError:
            pass

    # Clear non-admin users, keep only the Super Admin and Executive CEO
    cursor.execute("DELETE FROM users WHERE email NOT IN ('admin@cac-innovations.com', 'ceo@cac-innovations.com');")
    print("Cleared non-executive users.")

    # Reset auto-increment counters if sqlite_sequence exists
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('" + "', '".join(tables_to_clear) + "');")
    except sqlite3.OperationalError:
        pass
    
    # Re-enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    conn.commit()
    conn.execute("VACUUM;")
    conn.close()

    print("\n[SUCCESS] All business data, leads, projects, tasks, invoices, and submissions deleted!")
    print("[SUCCESS] Fresh start initialized: Clean database with only Super Admin (admin@cac-innovations.com) & core services ready!")

if __name__ == "__main__":
    reset_database()
