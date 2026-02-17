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
import sqlite3

class OnboardingStage(Enum):
    """Onboarding stages"""
    WELCOME = "welcome"
    PROFILE_SETUP = "profile_setup"
    TOUR_BASIC = "tour_basic"
    TOUR_CODE_GEN = "tour_code_gen"
    TOUR_IMAGE_TO_3D = "tour_image_to_3d"
    TOUR_AUDIO = "tour_audio"
    TOUR_VIDEO = "tour_video"
    TOUR_COLLABORATION = "tour_collaboration"
    FIRST_PROJECT = "first_project"
    COMPLETED = "completed"

class AIAssistant:
    """
    AI-powered interactive assistant for onboarding and help
    """
    
    def __init__(self, openai_key: str, db_path: str = "assistant.db"):
        self.openai_key = openai_key
        self.db_path = db_path
        self.session = None
        
        # Initialize database
        self._init_database()
        
        # Assistant personality
        self.personality = {
            "name": "ARIA",  # AI Rapid Interactive Assistant
            "tone": "friendly, helpful, encouraging",
            "style": "conversational, patient, supportive"
        }
        
        # Tutorial content
        self.tutorials = self._load_tutorials()
        
        # Tips library
        self.tips = self._load_tips()
        
    def _init_database(self):
        """Initialize database for tracking progress"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User onboarding progress
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS onboarding_progress (
                user_id INTEGER PRIMARY KEY,
                current_stage TEXT,
                completed_stages TEXT,
                started_at TEXT,
                completed_at TEXT,
                skip_count INTEGER DEFAULT 0,
                preferences TEXT
            )
        ''')
        
        # Tutorial completions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tutorial_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tutorial_id TEXT,
                completed_at TEXT,
                time_spent_seconds INTEGER,
                rating INTEGER
            )
        ''')
        
        # Assistant conversations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assistant_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                response TEXT,
                intent TEXT,
                helpful BOOLEAN,
                created_at TEXT
            )
        ''')
        
        # User achievements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_id TEXT,
                unlocked_at TEXT,
                notified BOOLEAN DEFAULT 0
            )
        ''')
        
        # Tips shown
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tips_shown (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tip_id TEXT,
                shown_at TEXT,
                dismissed BOOLEAN DEFAULT 0,
                helpful BOOLEAN
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def setup_session(self):
        """Initialize async session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close async session"""
        if self.session:
            await self.session.close()
    
    # ============================================
    # ONBOARDING SYSTEM
    # ============================================
    
    def start_onboarding(self, user_id: int) -> Dict[str, Any]:
        """Start onboarding for new user"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create onboarding record
        cursor.execute('''
            INSERT OR REPLACE INTO onboarding_progress 
            (user_id, current_stage, completed_stages, started_at, preferences)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            OnboardingStage.WELCOME.value,
            json.dumps([]),
            datetime.now().isoformat(),
            json.dumps({"show_tooltips": True, "auto_help": True})
        ))
        
        conn.commit()
        conn.close()
        
        # Return welcome message
        return self._get_stage_content(OnboardingStage.WELCOME)
    
    def get_onboarding_progress(self, user_id: int) -> Dict[str, Any]:
        """Get user's onboarding progress"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM onboarding_progress WHERE user_id = ?",
            (user_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {"stage": None, "completed": []}
        
        return {
            "user_id": row[0],
            "current_stage": row[1],
            "completed_stages": json.loads(row[2]),
            "started_at": row[3],
            "completed_at": row[4],
            "skip_count": row[5],
            "progress_percent": self._calculate_progress(json.loads(row[2]))
        }
    
    def next_onboarding_stage(self, user_id: int) -> Dict[str, Any]:
        """Move to next onboarding stage"""
        
        progress = self.get_onboarding_progress(user_id)
        current = progress.get("current_stage")
        
        # Get next stage
        stages = list(OnboardingStage)
        current_idx = next((i for i, s in enumerate(stages) if s.value == current), 0)
        next_stage = stages[min(current_idx + 1, len(stages) - 1)]
        
        # Update progress
        completed = progress.get("completed_stages", [])
        if current and current not in completed:
            completed.append(current)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE onboarding_progress
            SET current_stage = ?, completed_stages = ?, completed_at = ?
            WHERE user_id = ?
        ''', (
            next_stage.value,
            json.dumps(completed),
            datetime.now().isoformat() if next_stage == OnboardingStage.COMPLETED else None,
            user_id
        ))
        
        conn.commit()
        conn.close()
        
        # Check for achievements
        self._check_achievements(user_id, completed)
        
        return self._get_stage_content(next_stage)
    
    def skip_onboarding_stage(self, user_id: int) -> Dict[str, Any]:
        """Skip current stage"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE onboarding_progress
            SET skip_count = skip_count + 1
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        return self.next_onboarding_stage(user_id)
    
    def _get_stage_content(self, stage: OnboardingStage) -> Dict[str, Any]:
        """Get content for onboarding stage"""
        
        content = {
            OnboardingStage.WELCOME: {
                "title": "Welcome to AI Game Development Studio! 🎮",
                "message": f"""Hi! I'm {self.personality['name']}, your AI assistant!

I'm here to help you create amazing games using AI. Let me show you around!

What would you like to learn first?""",
                "options": [
                    {"id": "quick_start", "label": "Quick Start (5 min)", "icon": "⚡"},
                    {"id": "full_tour", "label": "Full Platform Tour (15 min)", "icon": "🎯"},
                    {"id": "skip", "label": "Skip - I'll explore myself", "icon": "🚀"}
                ],
                "video_url": "/tutorials/welcome.mp4",
                "interactive": True
            },
            
            OnboardingStage.PROFILE_SETUP: {
                "title": "Let's Set Up Your Profile 👤",
                "message": """Tell me a bit about yourself so I can personalize your experience!

What type of games do you want to create?""",
                "options": [
                    {"id": "fps", "label": "First-Person Shooter", "icon": "🔫"},
                    {"id": "rpg", "label": "RPG / Adventure", "icon": "⚔️"},
                    {"id": "platformer", "label": "Platformer", "icon": "🎮"},
                    {"id": "strategy", "label": "Strategy", "icon": "♟️"},
                    {"id": "other", "label": "Other / Multiple", "icon": "🎲"}
                ],
                "fields": [
                    {"name": "experience", "label": "Programming Experience", "type": "select",
                     "options": ["Beginner", "Intermediate", "Advanced"]},
                    {"name": "engine", "label": "Preferred Engine", "type": "select",
                     "options": ["Unreal Engine", "Unity", "Godot", "Custom"]},
                ]
            },
            
            OnboardingStage.TOUR_CODE_GEN: {
                "title": "AI Code Generation 💻",
                "message": """Let me show you how to generate C++ code with AI!

Just describe what you want in plain English, and I'll create it for you.

Try saying: "Create a character with health and damage"
""",
                "demo": {
                    "type": "interactive",
                    "component": "CodeGeneratorDemo",
                    "example_prompts": [
                        "Create a weapon with ammo and reload",
                        "Make a player controller with jump",
                        "Build an inventory system"
                    ]
                },
                "tips": [
                    "Be specific about what you want",
                    "You can ask follow-up questions",
                    "I'll validate and test the code automatically"
                ]
            },
            
            OnboardingStage.TOUR_IMAGE_TO_3D: {
                "title": "Image to 3D Models 🎨",
                "message": """Draw or upload an image, and I'll turn it into a 3D model!

This is perfect for:
• Character concepts
• Building designs
• Weapon sketches
• Environment ideas

Let's try it together!""",
                "demo": {
                    "type": "interactive",
                    "component": "ImageTo3DDemo",
                    "sample_images": [
                        "/samples/knight.png",
                        "/samples/castle.png",
                        "/samples/sword.png"
                    ]
                }
            },
            
            OnboardingStage.TOUR_AUDIO: {
                "title": "AI Audio Generation 🎵",
                "message": """Create music, sound effects, and voiceovers instantly!

What can you create?
• Background music (any genre)
• Sound effects (weapons, footsteps, etc.)
• Character voices
• Ambient sounds

Want to try creating battle music?""",
                "demo": {
                    "type": "interactive",
                    "component": "AudioGeneratorDemo"
                }
            },
            
            OnboardingStage.TOUR_VIDEO: {
                "title": "Video Editor for Cutscenes 🎬",
                "message": """Create cinematic cutscenes with our AI video editor!

You can:
• Generate cutscenes from scripts
• Edit existing footage
• Add effects and transitions
• Auto-edit with AI

Let me show you how to make a quick cutscene!""",
                "demo": {
                    "type": "interactive",
                    "component": "VideoEditorDemo"
                }
            },
            
            OnboardingStage.TOUR_COLLABORATION: {
                "title": "Team Collaboration 👥",
                "message": """Work together with your team in real-time!

Features:
• Share projects instantly
• Version control
• Real-time updates
• Role-based permissions

Want to invite a team member?""",
                "demo": {
                    "type": "info",
                    "features": [
                        "Project sharing",
                        "Real-time sync",
                        "Team chat",
                        "Asset library"
                    ]
                }
            },
            
            OnboardingStage.FIRST_PROJECT: {
                "title": "Create Your First Project! 🚀",
                "message": """You're ready to start creating!

Let's make your first project together. I'll guide you through every step.

What would you like to create first?""",
                "options": [
                    {"id": "character", "label": "Create a Character", "icon": "🦸"},
                    {"id": "level", "label": "Build a Level", "icon": "🏰"},
                    {"id": "cutscene", "label": "Make a Cutscene", "icon": "🎬"},
                    {"id": "audio", "label": "Generate Audio", "icon": "🎵"}
                ],
                "guided": True
            },
            
            OnboardingStage.COMPLETED: {
                "title": "Onboarding Complete! 🎉",
                "message": f"""Congratulations! You've completed the tour!

You're now ready to create amazing games with AI.

Remember, I'm always here to help. Just click the {self.personality['name']} button anytime!

Here are some resources to get started:
• Documentation
• Video Tutorials
• Community Forum
• Example Projects

Happy creating! 🎮""",
                "achievements_unlocked": ["Onboarding Complete", "First Steps"],
                "next_steps": [
                    "Create your first project",
                    "Join the community",
                    "Watch advanced tutorials"
                ]
            }
        }
        
        return content.get(stage, {
            "title": "Continue Your Journey",
            "message": "Let me know if you need any help!"
        })
    
    def _calculate_progress(self, completed_stages: List[str]) -> float:
        """Calculate onboarding progress percentage"""
        total_stages = len(OnboardingStage) - 1  # Exclude COMPLETED
        return (len(completed_stages) / total_stages) * 100 if total_stages > 0 else 0
    
    # ============================================
    # AI ASSISTANT CHAT
    # ============================================
    
    async def chat(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Chat with AI assistant
        """
        
        # Detect intent
        intent = await self._detect_intent(message, context)
        
        # Generate response
        response = await self._generate_response(message, intent, context)
        
        # Log conversation
        self._log_conversation(user_id, message, response, intent)
        
        # Check if help is needed
        suggestions = self._get_suggestions(intent, context)
        
        # Check for tips
        tips = self._get_contextual_tips(user_id, intent, context)
        
        return {
            "message": response,
            "intent": intent,
            "suggestions": suggestions,
            "tips": tips,
            "actions": self._get_quick_actions(intent)
        }
    
    async def _detect_intent(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Detect user intent from message"""
        
        message_lower = message.lower()
        
        # Common intents
        if any(word in message_lower for word in ["how do i", "how to", "can you show"]):
            return "help_request"
        
        if any(word in message_lower for word in ["create", "make", "generate", "build"]):
            return "creation_request"
        
        if any(word in message_lower for word in ["error", "broken", "not working", "bug"]):
            return "troubleshooting"
        
        if any(word in message_lower for word in ["what is", "explain", "tell me about"]):
            return "information_request"
        
        if any(word in message_lower for word in ["thanks", "thank you", "awesome", "great"]):
            return "positive_feedback"
        
        # Use AI for complex intent detection
        prompt = f"""Detect the user's intent from this message:

Message: "{message}"
Context: {json.dumps(context) if context else "None"}

Return one of: help_request, creation_request, troubleshooting, information_request, general_conversation

Intent:"""

        intent = await self._call_openai(prompt, max_tokens=50)
        return intent.strip().lower()
    
    async def _generate_response(
        self,
        message: str,
        intent: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate AI response"""
        
        # Build context-aware prompt
        system_prompt = f"""You are {self.personality['name']}, an AI assistant for a game development platform.

Personality: {self.personality['tone']}
Style: {self.personality['style']}

Your role:
- Help users learn the platform
- Answer questions clearly and concisely
- Guide users step-by-step
- Be encouraging and supportive
- Suggest features they might not know about

Current context: {json.dumps(context) if context else "New conversation"}
User intent: {intent}

Keep responses:
- Friendly and conversational
- Under 3 sentences for simple questions
- Include emojis sparingly
- Suggest next steps when appropriate"""

        user_prompt = f"User: {message}\n\n{self.personality['name']}:"
        
        response = await self._call_openai_chat(system_prompt, user_prompt)
        
        return response
    
    def _get_suggestions(
        self,
        intent: str,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Get contextual suggestions"""
        
        suggestions_map = {
            "help_request": [
                "Show me a video tutorial",
                "Give me step-by-step instructions",
                "Open the documentation"
            ],
            "creation_request": [
                "Use a template",
                "Show me examples",
                "Start guided creation"
            ],
            "troubleshooting": [
                "Check common solutions",
                "View error logs",
                "Contact support"
            ],
            "information_request": [
                "Show related features",
                "Open documentation",
                "Watch tutorial video"
            ]
        }
        
        return suggestions_map.get(intent, [
            "What can I create?",
            "Show me tutorials",
            "View examples"
        ])
    
    def _get_quick_actions(self, intent: str) -> List[Dict[str, str]]:
        """Get quick action buttons"""
        
        actions = {
            "help_request": [
                {"label": "📚 View Docs", "action": "open_docs"},
                {"label": "🎥 Watch Tutorial", "action": "open_tutorial"},
                {"label": "💬 Ask Community", "action": "open_forum"}
            ],
            "creation_request": [
                {"label": "✨ Start Creating", "action": "new_project"},
                {"label": "📋 Use Template", "action": "open_templates"},
                {"label": "🎯 View Examples", "action": "open_examples"}
            ],
            "troubleshooting": [
                {"label": "🔍 Check Logs", "action": "view_logs"},
                {"label": "🛠️ Common Fixes", "action": "open_troubleshooting"},
                {"label": "💌 Contact Support", "action": "contact_support"}
            ]
        }
        
        return actions.get(intent, [
            {"label": "🚀 Get Started", "action": "start_onboarding"},
            {"label": "📖 Learn More", "action": "open_docs"}
        ])
    
    # ============================================
    # CONTEXTUAL TIPS
    # ============================================
    
    def _get_contextual_tips(
        self,
        user_id: int,
        intent: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get contextual tip based on user action"""
        
        # Don't show too many tips
        if not self._should_show_tip(user_id):
            return None
        
        # Get relevant tip
        tip = self._find_relevant_tip(intent, context)
        
        if tip:
            self._log_tip_shown(user_id, tip["id"])
            return tip
        
        return None
    
    def _should_show_tip(self, user_id: int) -> bool:
        """Check if we should show a tip"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check recent tips
        cursor.execute('''
            SELECT COUNT(*) FROM tips_shown
            WHERE user_id = ? AND shown_at > datetime('now', '-1 hour')
        ''', (user_id,))
        
        recent_count = cursor.fetchone()[0]
        conn.close()
        
        # Max 3 tips per hour
        return recent_count < 3
    
    def _find_relevant_tip(
        self,
        intent: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find relevant tip"""
        
        # Filter tips by context
        relevant_tips = [
            tip for tip in self.tips
            if intent in tip.get("contexts", [])
        ]
        
        return relevant_tips[0] if relevant_tips else None
    
    def _log_tip_shown(self, user_id: int, tip_id: str):
        """Log that tip was shown"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tips_shown (user_id, tip_id, shown_at)
            VALUES (?, ?, ?)
        ''', (user_id, tip_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    # ============================================
    # ACHIEVEMENTS
    # ============================================
    
    def _check_achievements(self, user_id: int, completed_stages: List[str]):
        """Check and unlock achievements"""
        
        achievements = [
            {
                "id": "first_steps",
                "name": "First Steps",
                "description": "Complete your first onboarding stage",
                "condition": lambda stages: len(stages) >= 1
            },
            {
                "id": "quick_learner",
                "name": "Quick Learner",
                "description": "Complete onboarding in under 10 minutes",
                "condition": lambda stages: len(stages) == len(OnboardingStage) - 1
            },
            {
                "id": "explorer",
                "name": "Explorer",
                "description": "Complete all onboarding stages",
                "condition": lambda stages: OnboardingStage.COMPLETED.value in stages
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for achievement in achievements:
            if achievement["condition"](completed_stages):
                # Check if already unlocked
                cursor.execute(
                    "SELECT id FROM achievements WHERE user_id = ? AND achievement_id = ?",
                    (user_id, achievement["id"])
                )
                
                if not cursor.fetchone():
                    # Unlock achievement
                    cursor.execute('''
                        INSERT INTO achievements (user_id, achievement_id, unlocked_at)
                        VALUES (?, ?, ?)
                    ''', (user_id, achievement["id"], datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's achievements"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT achievement_id, unlocked_at FROM achievements WHERE user_id = ?",
            (user_id,)
        )
        
        achievements = []
        for row in cursor.fetchall():
            achievements.append({
                "id": row[0],
                "unlocked_at": row[1]
            })
        
        conn.close()
        return achievements
    
    # ============================================
    # TUTORIALS & TIPS
    # ============================================
    
    def _load_tutorials(self) -> Dict[str, Dict[str, Any]]:
        """Load tutorial content"""
        
        return {
            "code_generation": {
                "title": "AI Code Generation Basics",
                "duration": "5 min",
                "steps": [
                    "Open the Code Generator",
                    "Describe what you want in plain English",
                    "Review the generated code",
                    "Click 'Generate' to create files"
                ],
                "video_url": "/tutorials/code_generation.mp4"
            },
            "image_to_3d": {
                "title": "Turn Images into 3D Models",
                "duration": "7 min",
                "steps": [
                    "Upload or draw your concept",
                    "Add a description",
                    "Click 'Generate 3D Model'",
                    "Review and export"
                ],
                "video_url": "/tutorials/image_to_3d.mp4"
            },
            "audio_creation": {
                "title": "Create Game Audio with AI",
                "duration": "6 min",
                "steps": [
                    "Choose audio type (music/SFX/voice)",
                    "Describe what you want",
                    "Adjust settings",
                    "Generate and download"
                ],
                "video_url": "/tutorials/audio_creation.mp4"
            }
        }
    
    def _load_tips(self) -> List[Dict[str, Any]]:
        """Load tips library"""
        
        return [
            {
                "id": "keyboard_shortcuts",
                "title": "💡 Keyboard Shortcuts",
                "message": "Press Ctrl+K to quickly open the AI prompt anywhere!",
                "contexts": ["general_conversation"]
            },
            {
                "id": "save_often",
                "title": "💾 Auto-Save",
                "message": "Don't worry about saving - everything is auto-saved every 5 minutes!",
                "contexts": ["creation_request"]
            },
            {
                "id": "use_templates",
                "title": "📋 Use Templates",
                "message": "Save time by starting with a template! Check the Templates tab.",
                "contexts": ["creation_request"]
            },
            {
                "id": "ask_ai",
                "title": "🤖 Ask Me Anything",
                "message": "I can help with code, errors, ideas, and more. Just ask!",
                "contexts": ["help_request", "troubleshooting"]
            }
        ]
    
    def _log_conversation(
        self,
        user_id: int,
        message: str,
        response: str,
        intent: str
    ):
        """Log conversation for analytics"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO assistant_conversations
            (user_id, message, response, intent, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, message, response, intent, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    # ============================================
    # AI API CALLS
    # ============================================
    
    async def _call_openai(self, prompt: str, max_tokens: int = 500) -> str:
        """Call OpenAI API"""
        
        await self.setup_session()
        
        try:
            async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4-turbo-preview",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"I'm having trouble responding right now. Error: {str(e)}"
        
        return "I'm here to help! What would you like to know?"
    
    async def _call_openai_chat(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """Call OpenAI with system prompt"""
        
        await self.setup_session()
        
        try:
            async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4-turbo-preview",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 300,
                    "temperature": 0.8
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            return "I'm here to help! What would you like to know?"
        
        return "How can I assist you today?"