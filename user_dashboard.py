"""
User Dashboard - Database and User Management
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib
import os
import time
import threading

# Database lock for thread safety
_db_lock = threading.Lock()


class UserDashboard:
    """User dashboard and database management"""
    
    def __init__(self, db_path: str = "assistant.db"):
        """Initialize dashboard database"""
        self.db_path = db_path
        self.timeout = 10  # seconds
        self._init_db()
    
    def _get_connection(self):
        """Get database connection with timeout"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            conn.isolation_level = "DEFERRED"
            return conn
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                time.sleep(0.1)
                return self._get_connection()
            raise
    
    def _init_db(self):
        """Initialize database tables"""
        with _db_lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        last_login TEXT,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                # Projects table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'draft',
                        progress REAL DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Activity table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activity (
                        activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        description TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                conn.commit()
                conn.close()
                print("✓ Database initialized successfully")
            except Exception as e:
                print(f"Error initializing database: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Create a new user"""
        with _db_lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                password_hash = self._hash_password(password)
                now = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, created_at, last_login)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, email, password_hash, now, now))
                
                user_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                print(f"✓ User '{username}' created successfully")
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "message": f"User {username} created successfully"
                }
            
            except sqlite3.IntegrityError as e:
                if conn:
                    conn.close()
                print(f"User already exists: {email}")
                return {"success": False, "error": "User already exists"}
            except Exception as e:
                if conn:
                    conn.close()
                print(f"Error creating user: {e}")
                return {"success": False, "error": str(e)}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user"""
        with _db_lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                password_hash = self._hash_password(password)
                
                cursor.execute("""
                    SELECT user_id, username, email, created_at FROM users
                    WHERE email = ? AND password_hash = ? AND is_active = 1
                """, (email, password_hash))
                
                result = cursor.fetchone()
                
                if result:
                    user_id, username, user_email, created_at = result
                    
                    # Update last login
                    cursor.execute("""
                        UPDATE users SET last_login = ? WHERE user_id = ?
                    """, (datetime.now().isoformat(), user_id))
                    
                    conn.commit()
                    conn.close()
                    
                    print(f"✓ User '{username}' authenticated successfully")
                    
                    return {
                        "success": True,
                        "user_id": user_id,
                        "user": {
                            "user_id": user_id,
                            "username": username,
                            "email": user_email,
                            "created_at": created_at
                        }
                    }
                else:
                    conn.close()
                    print(f"Authentication failed for {email}")
                    return {"success": False, "error": "Invalid credentials"}
            
            except Exception as e:
                if conn:
                    conn.close()
                print(f"Error authenticating user: {e}")
                return {"success": False, "error": str(e)}
    
    def create_project(self, user_id: int, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new project"""
        with _db_lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT INTO projects (user_id, name, description, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, name, description, "active", now, now))
                
                project_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                print(f"✓ Project '{name}' created successfully")
                
                # Log activity
                self._log_activity(user_id, f"Created project: {name}")
                
                return {
                    "success": True,
                    "project_id": project_id,
                    "message": f"Project {name} created successfully"
                }
            
            except Exception as e:
                if conn:
                    conn.close()
                print(f"Error creating project: {e}")
                return {"success": False, "error": str(e)}
    
    def get_all_projects(self, user_id: int) -> Dict[str, Any]:
        """Get all projects for a user"""
        with _db_lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT project_id, name, description, status, progress, created_at
                    FROM projects
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
                
                rows = cursor.fetchall()
                conn.close()
                
                projects = []
                for row in rows:
                    projects.append({
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "status": row[3],
                        "progress": row[4],
                        "created_at": row[5],
                        "assets": 0,
                        "code_files": 0
                    })
                
                return {"projects": projects}
            
            except Exception as e:
                if conn:
                    conn.close()
                print(f"Error getting projects: {e}")
                return {"error": str(e)}
    
    def get_dashboard_overview(self, user_id: int) -> Dict[str, Any]:
        """Get dashboard overview for user"""
        with _db_lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Get user info
                cursor.execute("""
                    SELECT user_id, username, email, created_at FROM users WHERE user_id = ?
                """, (user_id,))
                user = cursor.fetchone()
                
                if not user:
                    return {"error": "User not found"}
                
                # Get projects count
                cursor.execute("""
                    SELECT COUNT(*) FROM projects WHERE user_id = ? AND status = 'active'
                """, (user_id,))
                total_projects = cursor.fetchone()[0]
                
                # Get activity
                cursor.execute("""
                    SELECT description, created_at FROM activity 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 20
                """, (user_id,))
                activity = cursor.fetchall()
                
                conn.close()
                
                return {
                    "user": {
                        "user_id": user[0],
                        "username": user[1],
                        "email": user[2],
                        "member_since": user[3]
                    },
                    "statistics": {
                        "total_projects": total_projects,
                        "completed_projects": 0,
                        "total_assets": 0,
                        "code_files": 0,
                        "achievements": 0
                    },
                    "storage": {
                        "used_mb": 0,
                        "limit_mb": 5000,
                        "percentage": 0
                    },
                    "quick_stats": {
                        "projects_this_month": 0,
                        "assets_this_month": 0,
                        "streak_days": 0
                    },
                    "recent_projects": [],
                    "recent_activity": [{"description": a[0], "timestamp": a[1]} for a in activity]
                }
            
            except Exception as e:
                if conn:
                    conn.close()
                print(f"Error getting dashboard overview: {e}")
                return {"error": str(e)}
    
    def get_activity_log(self, user_id: int) -> Dict[str, Any]:
        """Get activity log for user"""
        with _db_lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT description, created_at FROM activity 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 50
                """, (user_id,))
                
                rows = cursor.fetchall()
                conn.close()
                
                activity = []
                for row in rows:
                    activity.append({
                        "description": row[0],
                        "timestamp": row[1]
                    })
                
                return {"activity": activity}
            
            except Exception as e:
                if conn:
                    conn.close()
                print(f"Error getting activity log: {e}")
                return {"error": str(e)}
    
    def _log_activity(self, user_id: int, description: str):
        """Log user activity"""
        try:
            # Don't use the lock here to avoid deadlocks
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO activity (user_id, description, created_at)
                VALUES (?, ?, ?)
            """, (user_id, description, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error logging activity: {e}")