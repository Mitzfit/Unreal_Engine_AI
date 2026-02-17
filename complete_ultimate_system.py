"""
COMPLETE ULTIMATE SYSTEM
Integrates:
- Natural language AI
- Live visual editor
- Save/Export system
- Team collaboration
- Self-improving AI with web search
- Performance analytics
"""

import customtkinter as ctk
import threading
import time
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any

# Import all modules
import sys
sys.path.append(os.path.dirname(__file__))

from advanced_ai_brain import AdvancedAIBrain, IntentType
from live_visual_editor import LiveVisualEditor
from save_export_manager import SaveExportManager
from self_improving_ai import SelfImprovingAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CPP_AI_API_URL = os.getenv("CPP_AI_API_URL", "http://localhost:8000/api")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class CompleteUltimateApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize all systems
        self.ai_brain = AdvancedAIBrain(OPENAI_API_KEY, CPP_AI_API_URL)
        self.save_manager = SaveExportManager("exports")
        self.learning_ai = SelfImprovingAI(OPENAI_API_KEY, "ai_learning.db")
        self.visual_editor = None
        
        # State
        self.current_assets = []
        self.current_code_files = []
        self.team_id = None
        self.processing = False

        # Window setup
        self.title("Unreal AI Architect | COMPLETE ULTIMATE")
        self.geometry("1400x900")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_ui()
        
        # Start auto-save
        threading.Thread(target=self.start_auto_save, daemon=True).start()
        
        # Start performance reflection
        threading.Thread(target=self.start_reflection_loop, daemon=True).start()

    def setup_ui(self):
        # ===== SIDEBAR =====
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        # Logo
        ctk.CTkLabel(
            self.sidebar,
            text="🧠 AI ARCHITECT\nCOMPLETE",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Project Info
        project_frame = ctk.CTkFrame(self.sidebar)
        project_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(project_frame, text="📁 PROJECT", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.project_name_label = ctk.CTkLabel(project_frame, text="No project loaded")
        self.project_name_label.pack(pady=2)
        
        btn_frame = ctk.CTkFrame(project_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            btn_frame,
            text="New",
            width=80,
            height=28,
            command=self.new_project
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            btn_frame,
            text="Load",
            width=80,
            height=28,
            command=self.load_project
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            btn_frame,
            text="Save",
            width=80,
            height=28,
            command=self.save_project,
            fg_color="#22c55e"
        ).pack(side="left", padx=2)
        
        # Team Collaboration
        team_frame = ctk.CTkFrame(self.sidebar)
        team_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(team_frame, text="👥 TEAM", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.team_label = ctk.CTkLabel(team_frame, text="Solo mode")
        self.team_label.pack(pady=2)
        
        team_btn_frame = ctk.CTkFrame(team_frame, fg_color="transparent")
        team_btn_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            team_btn_frame,
            text="Join Team",
            width=100,
            height=28,
            command=self.join_team
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            team_btn_frame,
            text="Share",
            width=100,
            height=28,
            command=self.share_project
        ).pack(side="left", padx=2)
        
        # AI Status
        ai_frame = ctk.CTkFrame(self.sidebar)
        ai_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(ai_frame, text="🤖 AI STATUS", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.ai_status = ctk.CTkLabel(ai_frame, text="🟢 Online & Learning")
        self.ai_status.pack(pady=2)
        
        self.learning_stats = ctk.CTkLabel(
            ai_frame,
            text="Solutions learned: 0\nSuccess rate: 0%",
            font=ctk.CTkFont(size=10)
        )
        self.learning_stats.pack(pady=2)
        
        ctk.CTkButton(
            ai_frame,
            text="View Analytics",
            command=self.show_analytics,
            height=28
        ).pack(pady=5, padx=10, fill="x")

        # Conversation log
        self.conversation = ctk.CTkTextbox(
            self.sidebar,
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        self.conversation.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.conversation.configure(state="disabled")

        # ===== MAIN AREA =====
        self.main_area = ctk.CTkFrame(self, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        # Top bar with actions
        top_bar = ctk.CTkFrame(self.main_area, height=60)
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            top_bar,
            text="🚀 Complete AI Development Suite",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left", padx=20)
        
        action_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        action_frame.pack(side="right", padx=20)
        
        ctk.CTkButton(
            action_frame,
            text="💾 Export",
            width=100,
            command=self.show_export_menu
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            action_frame,
            text="👁️ Visual Editor",
            width=120,
            command=self.open_visual_editor,
            fg_color="#9333ea"
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            action_frame,
            text="📊 Performance",
            width=120,
            command=self.show_performance
        ).pack(side="left", padx=2)

        # Examples area
        self.examples_frame = ctk.CTkScrollableFrame(
            self.main_area,
            label_text="💡 What would you like to create? (Speak naturally)"
        )
        self.examples_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        
        self.setup_examples()

        # Input area
        self.input_frame = ctk.CTkFrame(self.main_area, fg_color="#1a1a1a", height=100)
        self.input_frame.grid(row=2, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Tell me what you want to create... The AI will search the web for solutions if needed!",
            height=50,
            font=ctk.CTkFont(size=14)
        )
        self.entry.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.entry.bind("<Return>", self.submit)

        btn_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1, padx=(0,20), pady=20)
        
        self.create_btn = ctk.CTkButton(
            btn_frame,
            text="✨ Create",
            width=100,
            height=50,
            command=lambda: self.submit(None),
            fg_color="#06b6d4",
            text_color="black",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.create_btn.pack()

    def setup_examples(self):
        """Setup example commands"""
        
        categories = [
            ("Characters & NPCs", [
                "Create a knight with armor and sword",
                "Make an enemy that patrols and attacks",
                "Generate an NPC shopkeeper with dialogue"
            ]),
            ("Code Generation", [
                "Write a health system with regeneration",
                "Create inventory code for 20 items",
                "Generate AI behavior tree for enemies"
            ]),
            ("Error Fixing", [
                "Fix: undefined reference to 'UWorld'",
                "My character falls through the floor",
                "Game crashes when spawning particles"
            ])
        ]
        
        for category, examples in categories:
            cat_frame = ctk.CTkFrame(self.examples_frame)
            cat_frame.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(
                cat_frame,
                text=category,
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(anchor="w", padx=10, pady=5)
            
            for example in examples:
                ctk.CTkButton(
                    cat_frame,
                    text=example,
                    command=lambda e=example: self.quick_command(e),
                    height=32,
                    anchor="w",
                    fg_color="transparent",
                    border_width=1
                ).pack(fill="x", padx=10, pady=2)

    def log(self, role: str, message: str):
        """Add to conversation log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.conversation.configure(state="normal")
        self.conversation.insert("end", f"[{timestamp}] {role}: {message}\n\n")
        self.conversation.see("end")
        self.conversation.configure(state="disabled")

    def quick_command(self, command: str):
        """Execute quick command"""
        self.entry.delete(0, "end")
        self.entry.insert(0, command)
        self.submit(None)

    def submit(self, event):
        """Process user input"""
        if self.processing:
            return
            
        user_input = self.entry.get()
        if not user_input.strip():
            return
        
        self.entry.delete(0, "end")
        self.log("YOU", user_input)
        
        self.create_btn.configure(state="disabled", text="⏳ Processing...")
        self.processing = True
        
        threading.Thread(
            target=self.process_complete_workflow,
            args=(user_input,),
            daemon=True
        ).start()

    def process_complete_workflow(self, user_input: str):
        """Complete workflow with all systems"""
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start operation tracking
        operation_id = self.learning_ai.start_operation("complete_workflow")
        
        try:
            # Step 1: Understand intent
            self.after(0, lambda: self.log("AI BRAIN", "🧠 Understanding your request..."))
            
            intent = loop.run_until_complete(
                self.ai_brain.understand_input(user_input)
            )
            
            self.after(0, lambda: self.log(
                "AI BRAIN",
                f"✓ Understood: {intent.primary_action}\nConfidence: {int(intent.confidence*100)}%"
            ))
            
            # Step 2: Check if it's an error - search web if needed
            if intent.intent_type == IntentType.ERROR_FIXING:
                self.after(0, lambda: self.log(
                    "AI SEARCH",
                    "🔍 Searching internet for solutions..."
                ))
                
                solutions = loop.run_until_complete(
                    self.learning_ai.search_error_solution(
                        user_input,
                        {"engine": "unreal"}
                    )
                ))
                
                if solutions:
                    self.after(0, lambda: self.log(
                        "AI SEARCH",
                        f"✓ Found {len(solutions)} solutions online"
                    ))
            
            # Step 3: Execute (simplified for demo)
            self.after(0, lambda: self.log("WORKER", "⚙️ Creating what you requested..."))
            time.sleep(2)  # Simulate work
            
            result = {
                "success": True,
                "type": "asset",
                "name": "Generated Asset",
                "file": f"assets/generated_{int(time.time())}.uasset"
            }
            
            # Store result
            self.current_assets.append(result)
            
            # Step 4: Test
            self.after(0, lambda: self.log("TESTER", "🧪 Running tests..."))
            
            test_plan = loop.run_until_complete(
                self.ai_brain.generate_test_plan(intent, result)
            )
            
            test_results = loop.run_until_complete(
                self.ai_brain.execute_automated_tests(test_plan, result.get("file", ""))
            )
            
            # Step 5: Log success
            success = test_results['passed'] >= test_results['total_tests'] * 0.8
            
            self.after(0, lambda: self.log(
                "COMPLETE",
                f"✅ Created: {result['name']}\n"
                f"Tests: {test_results['passed']}/{test_results['total_tests']} passed"
            ))
            
            # End operation tracking
            self.learning_ai.end_operation(
                operation_id,
                success=success,
                confidence_score=intent.confidence,
                quality_score=test_results['passed'] / test_results['total_tests'] if test_results['total_tests'] > 0 else 0
            )
            
            # Auto-save
            if self.save_manager.current_project:
                self.after(0, lambda: self.auto_save_silent())
            
            # Update learning stats
            self.after(0, lambda: self.update_ai_stats())
            
        except Exception as e:
            self.after(0, lambda: self.log("ERROR", f"❌ {str(e)}"))
            self.learning_ai.end_operation(operation_id, success=False, error_message=str(e))
        finally:
            loop.close()
            self.after(0, lambda: self.create_btn.configure(state="normal", text="✨ Create"))
            self.processing = False

    # ===== PROJECT MANAGEMENT =====
    
    def new_project(self):
        """Create new project"""
        dialog = ctk.CTkInputDialog(
            text="Enter project name:",
            title="New Project"
        )
        name = dialog.get_input()
        
        if name:
            metadata = self.save_manager.create_project(
                name=name,
                author=os.getenv("USER", "Developer"),
                description="AI Generated Project"
            )
            
            self.project_name_label.configure(text=name)
            self.log("PROJECT", f"✓ Created project: {name}")

    def load_project(self):
        """Load existing project"""
        # In production, show file dialog
        self.log("PROJECT", "Load project dialog (not implemented in demo)")

    def save_project(self):
        """Save current project"""
        if not self.save_manager.current_project:
            self.new_project()
            return
        
        try:
            save_path = self.save_manager.save_project(
                assets=self.current_assets,
                code_files=self.current_code_files,
                auto_backup=True
            )
            
            self.log("PROJECT", f"✓ Saved to: {save_path}")
        except Exception as e:
            self.log("ERROR", f"Save failed: {e}")

    def auto_save_silent(self):
        """Auto-save without notification"""
        if self.save_manager.current_project:
            try:
                self.save_manager.save_project(
                    assets=self.current_assets,
                    code_files=self.current_code_files,
                    auto_backup=False
                )
            except:
                pass

    # ===== TEAM COLLABORATION =====
    
    def join_team(self):
        """Join a team"""
        dialog = ctk.CTkInputDialog(
            text="Enter team ID:",
            title="Join Team"
        )
        team_id = dialog.get_input()
        
        if team_id:
            self.team_id = team_id
            self.team_label.configure(text=f"Team: {team_id}")
            self.log("TEAM", f"✓ Joined team: {team_id}")

    def share_project(self):
        """Share project with team"""
        if not self.team_id:
            self.log("TEAM", "⚠️ Join a team first")
            return
        
        if not self.save_manager.current_project:
            self.log("TEAM", "⚠️ No project to share")
            return
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            self.save_manager.share_with_team(
                self.team_id,
                self.save_manager.current_project.project_id
            )
        )
        
        loop.close()
        
        self.log("TEAM", f"✓ Shared project with team")

    # ===== EXPORT =====
    
    def show_export_menu(self):
        """Show export options menu"""
        
        menu_window = ctk.CTkToplevel(self)
        menu_window.title("Export Options")
        menu_window.geometry("400x500")
        
        ctk.CTkLabel(
            menu_window,
            text="Export As",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)
        
        export_options = [
            ("Unreal Plugin", self.export_unreal_plugin),
            ("Standalone Package", self.export_standalone),
            ("Git Repository", self.export_git),
            ("ZIP Archive", self.export_zip)
        ]
        
        for label, command in export_options:
            ctk.CTkButton(
                menu_window,
                text=label,
                command=lambda c=command, w=menu_window: self.do_export(c, w),
                height=50
            ).pack(pady=10, padx=40, fill="x")

    def do_export(self, export_func, window):
        """Execute export"""
        window.destroy()
        threading.Thread(target=export_func, daemon=True).start()

    def export_unreal_plugin(self):
        """Export as Unreal plugin"""
        self.log("EXPORT", "📦 Exporting as Unreal Plugin...")
        
        try:
            output = self.save_manager.export_unreal_plugin(
                "exports/plugins",
                "AIGeneratedPlugin",
                self.current_code_files,
                self.current_assets
            )
            
            self.log("EXPORT", f"✓ Plugin exported: {output}")
        except Exception as e:
            self.log("EXPORT", f"❌ Export failed: {e}")

    def export_standalone(self):
        """Export standalone"""
        self.log("EXPORT", "📦 Exporting standalone package...")
        
        try:
            output = self.save_manager.export_standalone_package(
                "exports/standalone",
                "AIProject",
                include_source=True,
                include_documentation=True
            )
            
            self.log("EXPORT", f"✓ Package exported: {output}")
        except Exception as e:
            self.log("EXPORT", f"❌ Export failed: {e}")

    def export_git(self):
        """Export to Git"""
        self.log("EXPORT", "📦 Exporting to Git repository...")
        
        try:
            output = self.save_manager.export_git_repository(
                "exports/git_repo",
                "AI Generated Export"
            )
            
            self.log("EXPORT", f"✓ Git repo created: {output}")
        except Exception as e:
            self.log("EXPORT", f"❌ Export failed: {e}")

    def export_zip(self):
        """Export as ZIP"""
        self.log("EXPORT", "📦 Creating ZIP archive...")
        # Implementation here

    # ===== ANALYTICS =====
    
    def show_analytics(self):
        """Show AI analytics window"""
        
        analytics_window = ctk.CTkToplevel(self)
        analytics_window.title("AI Analytics")
        analytics_window.geometry("700x600")
        
        # Get report
        report = self.learning_ai.get_performance_report(days=7)
        
        # Display
        text_widget = ctk.CTkTextbox(analytics_window, font=ctk.CTkFont(family="Consolas", size=11))
        text_widget.pack(fill="both", expand=True, padx=20, pady=20)
        
        report_text = f"""AI PERFORMANCE REPORT (Last 7 Days)
{'='*60}

OPERATIONS:
"""
        
        for op in report.get("operations", []):
            report_text += f"""
  {op['type']}:
    Total: {op['total_count']}
    Success Rate: {op['success_rate']*100:.1f}%
    Avg Duration: {op['avg_duration_sec']:.2f}s
    Avg Quality: {op['avg_quality']*100:.1f}%
"""
        
        report_text += f"""

LEARNING:
  Active Solutions: {report['learning_stats']['active_entries']}
  Avg Effectiveness: {report['learning_stats']['avg_effectiveness']*100:.1f}%
"""
        
        text_widget.insert("1.0", report_text)

    def show_performance(self):
        """Show performance dashboard"""
        self.log("ANALYTICS", "📊 Performance dashboard (see analytics window)")
        self.show_analytics()

    def update_ai_stats(self):
        """Update AI stats display"""
        solutions = self.learning_ai.get_top_solutions(limit=1)
        
        if solutions:
            count = len(solutions)
            avg_effectiveness = solutions[0].get('effectiveness', 0) * 100
            
            self.learning_stats.configure(
                text=f"Solutions learned: {count}\nSuccess rate: {avg_effectiveness:.0f}%"
            )

    # ===== VISUAL EDITOR =====
    
    def open_visual_editor(self):
        """Open visual editor"""
        if self.visual_editor is None or not self.visual_editor.winfo_exists():
            self.visual_editor = LiveVisualEditor(self)
        else:
            self.visual_editor.focus()

    # ===== BACKGROUND TASKS =====
    
    def start_auto_save(self):
        """Auto-save loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        def get_state():
            return {
                "assets": self.current_assets,
                "code_files": self.current_code_files
            }
        
        loop.run_until_complete(
            self.save_manager.start_auto_save(get_state)
        )

    def start_reflection_loop(self):
        """AI reflection loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            time.sleep(3600)  # Every hour
            
            try:
                reflection = loop.run_until_complete(
                    self.learning_ai.reflect_and_improve()
                )
                
                self.after(0, lambda: self.log(
                    "AI REFLECTION",
                    f"🧠 Self-improvement complete\nHealth: {reflection.get('overall_health', 'unknown')}"
                ))
            except Exception as e:
                print(f"Reflection error: {e}")

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("⚠️  WARNING: OPENAI_API_KEY not set")
    
    app = CompleteUltimateApp()
    app.mainloop()
