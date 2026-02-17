"""
User Authentication & Session Management System
Complete login/logout with automatic session tracking
"""

import sqlite3
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json

class UserAuthSystem:
    """
    Complete user authentication and session management
    """
    
    def __init__(self, db_path: str = "user_system.db"):
        self.db_path = db_path
        self.active_sessions = {}
        self._init_database()
    
    def _init_database(self):
        """Initialize user database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                created_at TEXT,
                last_login TEXT,
                total_sessions INTEGER DEFAULT 0,
                total_assets_created INTEGER DEFAULT 0,
                storage_used_mb REAL DEFAULT 0.0,
                preferences TEXT
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                session_token TEXT UNIQUE,
                start_time TEXT,
                end_time TEXT,
                duration_seconds INTEGER,
                ip_address TEXT,
                actions_log TEXT,
                assets_created TEXT,
                errors_encountered TEXT,
                features_used TEXT,
                status TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # User assets table (everything user creates)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_assets (
                asset_id TEXT PRIMARY KEY,
                user_id INTEGER,
                asset_type TEXT,
                asset_name TEXT,
                asset_data TEXT,
                file_path TEXT,
                file_size_mb REAL,
                tags TEXT,
                is_public INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                usage_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Shared asset library
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_asset_library (
                library_id TEXT PRIMARY KEY,
                original_asset_id TEXT,
                original_user_id INTEGER,
                asset_name TEXT,
                asset_type TEXT,
                description TEXT,
                preview_image TEXT,
                file_path TEXT,
                downloads INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                ratings_count INTEGER DEFAULT 0,
                tags TEXT,
                added_at TEXT,
                FOREIGN KEY (original_asset_id) REFERENCES user_assets(asset_id),
                FOREIGN KEY (original_user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register new user"""
        
        # Validate inputs
        if len(username) < 3:
            return {"success": False, "error": "Username must be at least 3 characters"}
        
        if len(password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters"}
        
        # Generate salt and hash password
        salt = secrets.token_hex(32)
        password_hash = self._hash_password(password, salt)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, full_name, created_at, preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                username,
                email,
                password_hash,
                salt,
                full_name or username,
                datetime.now().isoformat(),
                json.dumps({"theme": "dark", "auto_save": True, "notifications": True})
            ))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            return {
                "success": True,
                "user_id": user_id,
                "username": username,
                "message": "User registered successfully"
            }
            
        except sqlite3.IntegrityError as e:
            return {
                "success": False,
                "error": "Username or email already exists"
            }
        finally:
            conn.close()
    
    def login(
        self,
        username: str,
        password: str,
        ip_address: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """User login"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT user_id, password_hash, salt, username, email, full_name, role FROM users WHERE username = ?",
            (username,)
        )
        
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {"success": False, "error": "Invalid username or password"}
        
        # Verify password
        user_id, stored_hash, salt, username, email, full_name, role = user
        password_hash = self._hash_password(password, salt)
        
        if password_hash != stored_hash:
            conn.close()
            return {"success": False, "error": "Invalid username or password"}
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        session_id = self._generate_session_id()
        
        # Create session
        cursor.execute('''
            INSERT INTO user_sessions (session_id, user_id, session_token, start_time, ip_address, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            user_id,
            session_token,
            datetime.now().isoformat(),
            ip_address,
            "active"
        ))
        
        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = ?, total_sessions = total_sessions + 1 WHERE user_id = ?",
            (datetime.now().isoformat(), user_id)
        )
        
        conn.commit()
        conn.close()
        
        # Store active session
        self.active_sessions[session_token] = {
            "session_id": session_id,
            "user_id": user_id,
            "username": username,
            "start_time": time.time(),
            "actions": [],
            "assets_created": [],
            "errors": [],
            "features_used": set()
        }
        
        return {
            "success": True,
            "session_token": session_token,
            "user_id": user_id,
            "username": username,
            "email": email,
            "full_name": full_name,
            "role": role
        }
    
    def logout(
        self,
        session_token: str
    ) -> Dict[str, Any]:
        """User logout - returns session data for analysis"""
        
        if session_token not in self.active_sessions:
            return {"success": False, "error": "Invalid session"}
        
        session_data = self.active_sessions[session_token]
        session_id = session_data["session_id"]
        
        # Calculate duration
        duration = time.time() - session_data["start_time"]
        
        # Update session in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions
            SET end_time = ?, duration_seconds = ?, actions_log = ?, 
                assets_created = ?, errors_encountered = ?, features_used = ?, status = ?
            WHERE session_id = ?
        ''', (
            datetime.now().isoformat(),
            int(duration),
            json.dumps(session_data["actions"]),
            json.dumps(session_data["assets_created"]),
            json.dumps(session_data["errors"]),
            json.dumps(list(session_data["features_used"])),
            "completed",
            session_id
        ))
        
        conn.commit()
        conn.close()
        
        # Remove from active sessions
        del self.active_sessions[session_token]
        
        return {
            "success": True,
            "session_data": {
                "session_id": session_id,
                "user_id": session_data["user_id"],
                "start_time": datetime.fromtimestamp(session_data["start_time"]).isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration": duration,
                "actions": session_data["actions"],
                "assets_created": session_data["assets_created"],
                "errors": session_data["errors"],
                "features_used": list(session_data["features_used"])
            }
        }
    
    def track_action(
        self,
        session_token: str,
        action_type: str,
        details: Dict[str, Any]
    ):
        """Track user action in session"""
        
        if session_token in self.active_sessions:
            self.active_sessions[session_token]["actions"].append({
                "type": action_type,
                "details": details,
                "timestamp": time.time()
            })
    
    def track_asset_created(
        self,
        session_token: str,
        asset_data: Dict[str, Any]
    ):
        """Track asset creation"""
        
        if session_token in self.active_sessions:
            self.active_sessions[session_token]["assets_created"].append(asset_data)
    
    def track_feature_used(
        self,
        session_token: str,
        feature_name: str
    ):
        """Track feature usage"""
        
        if session_token in self.active_sessions:
            self.active_sessions[session_token]["features_used"].add(feature_name)
    
    def track_error(
        self,
        session_token: str,
        error_data: Dict[str, Any]
    ):
        """Track error occurrence"""
        
        if session_token in self.active_sessions:
            self.active_sessions[session_token]["errors"].append(error_data)
    
    def save_user_asset(
        self,
        user_id: int,
        asset_type: str,
        asset_name: str,
        asset_data: Dict[str, Any],
        file_path: str,
        tags: List[str] = None,
        is_public: bool = False
    ) -> str:
        """Save user-created asset to database"""
        
        asset_id = self._generate_asset_id()
        
        # Calculate file size (simplified)
        file_size_mb = 0.1  # Placeholder
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            asset_id,
            user_id,
            asset_type,
            asset_name,
            json.dumps(asset_data),
            file_path,
            file_size_mb,
            json.dumps(tags or []),
            1 if is_public else 0,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            0
        ))
        
        # Update user stats
        cursor.execute('''
            UPDATE users 
            SET total_assets_created = total_assets_created + 1,
                storage_used_mb = storage_used_mb + ?
            WHERE user_id = ?
        ''', (file_size_mb, user_id))
        
        conn.commit()
        conn.close()
        
        return asset_id
    
    def get_user_assets(
        self,
        user_id: int,
        asset_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all assets created by user"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if asset_type:
            cursor.execute(
                "SELECT * FROM user_assets WHERE user_id = ? AND asset_type = ? ORDER BY created_at DESC",
                (user_id, asset_type)
            )
        else:
            cursor.execute(
                "SELECT * FROM user_assets WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
        
        assets = []
        for row in cursor.fetchall():
            assets.append({
                "asset_id": row[0],
                "asset_type": row[2],
                "asset_name": row[3],
                "asset_data": json.loads(row[4]),
                "file_path": row[5],
                "tags": json.loads(row[7]),
                "is_public": bool(row[8]),
                "created_at": row[9],
                "usage_count": row[11]
            })
        
        conn.close()
        return assets
    
    def share_asset_to_library(
        self,
        asset_id: str,
        description: str
    ) -> bool:
        """Share user asset to community library"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get asset
        cursor.execute("SELECT * FROM user_assets WHERE asset_id = ?", (asset_id,))
        asset = cursor.fetchone()
        
        if not asset:
            conn.close()
            return False
        
        # Add to shared library
        library_id = self._generate_asset_id()
        
        cursor.execute('''
            INSERT INTO shared_asset_library VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            library_id,
            asset[0],  # asset_id
            asset[1],  # user_id
            asset[3],  # asset_name
            asset[2],  # asset_type
            description,
            None,  # preview_image
            asset[5],  # file_path
            0,  # downloads
            0.0,  # rating
            0,  # ratings_count
            asset[7],  # tags
            datetime.now().isoformat()
        ))
        
        # Mark asset as public
        cursor.execute("UPDATE user_assets SET is_public = 1 WHERE asset_id = ?", (asset_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    def search_shared_library(
        self,
        query: str = "",
        asset_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search community asset library"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        sql = "SELECT * FROM shared_asset_library WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (asset_name LIKE ? OR description LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        
        if asset_type:
            sql += " AND asset_type = ?"
            params.append(asset_type)
        
        sql += " ORDER BY downloads DESC, rating DESC LIMIT 100"
        
        cursor.execute(sql, params)
        
        assets = []
        for row in cursor.fetchall():
            assets.append({
                "library_id": row[0],
                "asset_name": row[3],
                "asset_type": row[4],
                "description": row[5],
                "file_path": row[7],
                "downloads": row[8],
                "rating": row[9],
                "tags": json.loads(row[11]) if row[11] else []
            })
        
        conn.close()
        return assets
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {}
        
        cursor.execute(
            "SELECT COUNT(*), asset_type FROM user_assets WHERE user_id = ? GROUP BY asset_type",
            (user_id,)
        )
        
        assets_by_type = {row[1]: row[0] for row in cursor.fetchall()}
        
        cursor.execute(
            "SELECT COUNT(*) FROM shared_asset_library WHERE original_user_id = ?",
            (user_id,)
        )
        
        shared_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "username": user[1],
            "full_name": user[5],
            "member_since": user[7],
            "total_sessions": user[9],
            "total_assets": user[10],
            "storage_used_mb": user[11],
            "assets_by_type": assets_by_type,
            "shared_assets": shared_count
        }
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _generate_session_id(self) -> str:
        """Generate session ID"""
        return f"sess_{secrets.token_hex(16)}"
    
    def _generate_asset_id(self) -> str:
        """Generate asset ID"""
        return f"asset_{secrets.token_hex(12)}"
