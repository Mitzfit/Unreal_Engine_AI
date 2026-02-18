"""
AI Assistant & Onboarding System
Interactive guide that helps users learn and use the platform
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import sys

# Make sure these are also imported
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from user_dashboard import UserDashboard
except ImportError:
    UserDashboard = None

try:
    from advanced_ai_brain import AdvancedAIBrain
except ImportError:
    AdvancedAIBrain = None


class AuthState(Enum):
    """Authentication state enumeration"""
    LOGGED_OUT = "logged_out"
    LOGGED_IN = "logged_in"
    PENDING = "pending"
    ERROR = "error"


@dataclass
class User:
    """User data class"""
    user_id: int
    username: str
    email: str
    created_at: str
    last_login: str
    is_active: bool = True


class AIAssistant:
    """AI Assistant with authentication and dashboard integration"""
    
    def __init__(self, openai_key: str = "", db_path: str = "assistant.db"):
        """Initialize AI Assistant"""
        self.openai_key = openai_key
        self.db_path = db_path
        self.auth_state = AuthState.LOGGED_OUT
        self.current_user: Optional[User] = None
        self.dashboard = None
        
        # Initialize database
        try:
            if UserDashboard:
                self.dashboard = UserDashboard(db_path=db_path)
            else:
                print("⚠️  UserDashboard not available")
        except Exception as e:
            print(f"Error initializing dashboard: {e}")
            self.dashboard = None
    
    def register_user(self, username: str, email: str, password: str) -> tuple:
        """Register a new user"""
        try:
            if not self.dashboard:
                return False, {"error": "Dashboard not initialized"}
            
            result = self.dashboard.create_user(username, email, password)
            
            if result.get("success"):
                self.auth_state = AuthState.LOGGED_IN
                self.current_user = User(
                    user_id=result["user_id"],
                    username=username,
                    email=email,
                    created_at=datetime.now().isoformat(),
                    last_login=datetime.now().isoformat(),
                    is_active=True
                )
                return True, result
            else:
                self.auth_state = AuthState.ERROR
                return False, result
        
        except Exception as e:
            self.auth_state = AuthState.ERROR
            return False, {"error": str(e)}
    
    def login_user(self, email: str, password: str) -> tuple:
        """Login user"""
        try:
            if not self.dashboard:
                return False, {"error": "Dashboard not initialized"}
            
            result = self.dashboard.authenticate_user(email, password)
            
            if result.get("success"):
                self.auth_state = AuthState.LOGGED_IN
                user_data = result.get("user", {})
                self.current_user = User(
                    user_id=user_data.get("user_id", 1),
                    username=user_data.get("username", "User"),
                    email=email,
                    created_at=user_data.get("created_at", datetime.now().isoformat()),
                    last_login=datetime.now().isoformat(),
                    is_active=True
                )
                return True, result
            else:
                self.auth_state = AuthState.ERROR
                return False, result
        
        except Exception as e:
            self.auth_state = AuthState.ERROR
            return False, {"error": str(e)}
    
    def logout_user(self) -> bool:
        """Logout current user"""
        self.auth_state = AuthState.LOGGED_OUT
        self.current_user = None
        return True
    
    def create_new_project(self, user_id: int, name: str, description: str = "") -> dict:
        """Create a new project"""
        try:
            if not self.dashboard:
                return {"success": False, "error": "Dashboard not initialized"}
            
            result = self.dashboard.create_project(user_id, name, description)
            return result
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_projects(self, user_id: int) -> dict:
        """Get all projects for a user"""
        try:
            if not self.dashboard:
                return {"error": "Dashboard not initialized"}
            
            return self.dashboard.get_all_projects(user_id)
        
        except Exception as e:
            return {"error": str(e)}
    
    def guest_login(self) -> tuple:
        """Create a guest login session"""
        try:
            result = self.register_user(
                username="Guest User",
                email=f"guest_{datetime.now().timestamp()}@guest.local",
                password="guest123"
            )
            return result
        
        except Exception as e:
            return False, {"error": str(e)}