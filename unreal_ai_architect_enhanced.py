"""
Unreal AI Architect - Enhanced Edition
Integrated with C++ AI Automation Platform features:
- Advanced code generation with validation
- AI-powered error handling
- Iterative refinement
- Build system generation
- Engine compatibility checks
"""

import customtkinter as ctk
import socket
import json
import threading
import time
import os
import asyncio
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any
import re

# --- CONFIGURATION ---
load_dotenv()

UNREAL_HOST = os.getenv("UNREAL_HOST", "127.0.0.1")
UNREAL_PORT = int(os.getenv("UNREAL_PORT", 30010))

# C++ AI Platform API Configuration
CPP_AI_API_URL = os.getenv("CPP_AI_API_URL", "http://localhost:8000/api")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# Ensure output directories exist
os.makedirs("assets/models", exist_ok=True)
os.makedirs("assets/audio", exist_ok=True)
os.makedirs("assets/scripts", exist_ok=True)
os.makedirs("assets/code_generated", exist_ok=True)
os.makedirs("assets/build_files", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# --- 1. ENHANCED DIRECTOR BRAIN (With C++ AI Integration) ---
class EnhancedDirectorBrain:
    def __init__(self):
        self.api_url = CPP_AI_API_URL
        self.session = None
        self.current_project_id = None
        self.auth_token = None
        
    def analyze_intent(self, prompt):
        """
        Enhanced intent analysis with C++ AI platform integration
        """
        prompt_lower = prompt.lower()
        tasks = []

        # C++ Code Generation (Enhanced)
        if any(word in prompt_lower for word in ["code", "script", "class", "actor", "component", "c++"]):
            tasks.append({
                "worker": "ARCHITECT_PRO", 
                "action": "generate_cpp_advanced",
                "details": prompt,
                "features": {
                    "validation": True,
                    "build_files": True,
                    "error_check": True,
                    "optimization": True
                }
            })
        
        # Error Analysis and Fixing
        if any(word in prompt_lower for word in ["error", "fix", "debug", "crash", "compile"]):
            tasks.append({
                "worker": "ERROR_DOCTOR",
                "action": "analyze_and_fix",
                "details": prompt
            })
        
        # Code Refinement
        if any(word in prompt_lower for word in ["refine", "improve", "optimize", "better"]):
            tasks.append({
                "worker": "ARCHITECT_PRO",
                "action": "refine_code",
                "details": prompt
            })
        
        # Build System Generation
        if any(word in prompt_lower for word in ["build", "module", ".build.cs", "dependencies"]):
            tasks.append({
                "worker": "BUILD_MASTER",
                "action": "generate_build_files",
                "details": prompt
            })

        # Asset Generation (Original)
        if any(word in prompt_lower for word in ["asset", "model", "mesh"]):
            tasks.append({
                "worker": "GENESIS", 
                "action": "generate_3d",
                "details": prompt
            })
        
        # Audio Generation (Original)
        if any(word in prompt_lower for word in ["music", "sound", "audio"]):
            tasks.append({
                "worker": "SYMPHONY",
                "action": "compose_music",
                "details": prompt
            })
            
        # Level Editing (Original)
        if any(word in prompt_lower for word in ["level", "light", "scene"]):
            tasks.append({
                "worker": "HOLODECK",
                "action": "edit_level",
                "details": prompt
            })

        # Marketing (Original)
        if "trailer" in prompt_lower:
            tasks.append({
                "worker": "HYPE_BEAST",
                "action": "edit_trailer",
                "details": prompt
            })
            
        # Default
        if not tasks:
            tasks.append({
                "worker": "DIRECTOR",
                "action": "acknowledge",
                "details": "Processing general request..."
            })
            
        return tasks
    
    async def setup_session(self):
        """Setup aiohttp session for API calls"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

# --- 2. UNREAL BRIDGE (Enhanced) ---
class EnhancedUnrealBridge:
    def __init__(self):
        self.host = UNREAL_HOST
        self.port = UNREAL_PORT
        self.connected = False
        
    def send_command(self, command, data):
        """Send command to Unreal Engine"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect((self.host, self.port))
                msg = json.dumps({"cmd": command, "data": data})
                s.sendall(msg.encode('utf-8'))
                self.connected = True
                return True
        except ConnectionRefusedError:
            self.connected = False
            return False
        except Exception as e:
            print(f"Bridge Error: {e}")
            self.connected = False
            return False
    
    def import_cpp_code(self, file_path, module_name):
        """Import generated C++ code into Unreal project"""
        return self.send_command("IMPORT_CPP", {
            "file_path": file_path,
            "module_name": module_name,
            "regenerate_project": True
        })
    
    def import_build_files(self, build_file_path):
        """Import .Build.cs files"""
        return self.send_command("IMPORT_BUILD", {
            "file_path": build_file_path
        })

# --- 3. ENHANCED WORKERS (With C++ AI Platform Integration) ---
class EnhancedWorkers:
    def __init__(self, api_url, auth_token=None):
        self.api_url = api_url
        self.auth_token = auth_token
        self.session = None
        
    async def setup_session(self):
        """Setup async HTTP session"""
        if not self.session:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            self.session = aiohttp.ClientSession(headers=headers)
    
    async def architect_pro_generate(self, details, features):
        """
        Advanced C++ code generation with validation and build files
        Integrates with C++ AI Platform API
        """
        await self.setup_session()
        
        try:
            # Generate code with AI
            async with self.session.post(
                f"{self.api_url}/code/generate",
                json={
                    "prompt": details,
                    "engine_type": "unreal",
                    "project_id": 1,  # Default project
                    "ai_model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "include_comments": True,
                    "optimize_code": features.get("optimization", True)
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Save generated code
                    timestamp = int(time.time())
                    filename = f"assets/code_generated/Generated_{timestamp}.cpp"
                    header_filename = f"assets/code_generated/Generated_{timestamp}.h"
                    
                    with open(filename, 'w') as f:
                        f.write(result.get("generated_code", ""))
                    
                    output = {
                        "cpp_file": filename,
                        "header_file": header_filename,
                        "validation": result.get("metadata", {}).get("validation", {}),
                        "quality_score": result.get("metadata", {}).get("quality_score", 0),
                        "requires_review": result.get("metadata", {}).get("requires_review", True),
                        "code_id": result.get("id")
                    }
                    
                    # Generate build files if requested
                    if features.get("build_files"):
                        build_result = await self.generate_build_files(result.get("id"))
                        output["build_files"] = build_result
                    
                    return output
                else:
                    return {"error": f"API returned status {response.status}"}
                    
        except Exception as e:
            return {"error": f"Code generation failed: {str(e)}"}
    
    async def error_doctor_analyze(self, details):
        """
        AI-powered error analysis and automatic fixing
        """
        await self.setup_session()
        
        # Extract error message and code context from details
        error_message = details
        code_context = ""
        
        # Try to read from last generated file if exists
        code_files = sorted([f for f in os.listdir("assets/code_generated") if f.endswith(".cpp")])
        if code_files:
            with open(f"assets/code_generated/{code_files[-1]}", 'r') as f:
                code_context = f.read()
        
        try:
            # Analyze error
            async with self.session.post(
                f"{self.api_url}/error-handling/analyze",
                json={
                    "error_message": error_message,
                    "code_context": code_context,
                    "engine_type": "unreal"
                }
            ) as response:
                if response.status == 200:
                    analysis = await response.json()
                    
                    # Attempt auto-fix if confidence is high
                    if analysis.get("confidence_score", 0) > 0.7:
                        fix_result = await self.auto_fix_error(
                            analysis.get("error_id"),
                            code_context
                        )
                        analysis["auto_fix"] = fix_result
                    
                    return analysis
                else:
                    return {"error": f"Analysis failed with status {response.status}"}
                    
        except Exception as e:
            return {"error": f"Error analysis failed: {str(e)}"}
    
    async def auto_fix_error(self, error_id, code):
        """
        Automatically fix an analyzed error
        """
        await self.setup_session()
        
        try:
            async with self.session.post(
                f"{self.api_url}/error-handling/auto-fix",
                json={
                    "error_analysis_id": error_id,
                    "code": code,
                    "fix_strategy": "conservative"
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Save fixed code
                    if result.get("success") and result.get("fixed_code"):
                        timestamp = int(time.time())
                        filename = f"assets/code_generated/Fixed_{timestamp}.cpp"
                        with open(filename, 'w') as f:
                            f.write(result["fixed_code"])
                        result["saved_to"] = filename
                    
                    return result
                else:
                    return {"error": f"Auto-fix failed with status {response.status}"}
                    
        except Exception as e:
            return {"error": f"Auto-fix failed: {str(e)}"}
    
    async def refine_code(self, code_id, feedback):
        """
        Iteratively refine generated code
        """
        await self.setup_session()
        
        try:
            async with self.session.post(
                f"{self.api_url}/code/refine/{code_id}",
                json={
                    "code_id": code_id,
                    "user_feedback": feedback,
                    "issues_to_fix": []
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Save refined code
                    if result.get("refined_code"):
                        timestamp = int(time.time())
                        filename = f"assets/code_generated/Refined_{timestamp}.cpp"
                        with open(filename, 'w') as f:
                            f.write(result["refined_code"]["generated_code"])
                        result["saved_to"] = filename
                    
                    return result
                else:
                    return {"error": f"Refinement failed with status {response.status}"}
                    
        except Exception as e:
            return {"error": f"Refinement failed: {str(e)}"}
    
    async def generate_build_files(self, code_id):
        """
        Generate .Build.cs and other build system files
        """
        await self.setup_session()
        
        try:
            async with self.session.post(
                f"{self.api_url}/code/{code_id}/build-files",
                json={"dependencies": ["Core", "CoreUObject", "Engine"]}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Save build files
                    saved_files = {}
                    for filename, content in result.get("files", {}).items():
                        filepath = f"assets/build_files/{filename}"
                        with open(filepath, 'w') as f:
                            f.write(content)
                        saved_files[filename] = filepath
                    
                    return {
                        "files": saved_files,
                        "instructions": result.get("instructions", "")
                    }
                else:
                    return {"error": f"Build file generation failed with status {response.status}"}
                    
        except Exception as e:
            return {"error": f"Build file generation failed: {str(e)}"}
    
    # Original workers (unchanged)
    def genesis_generate(self, details):
        time.sleep(2) 
        filename = f"assets/models/{details.replace(' ', '_')[:10]}.glb"
        with open(filename, 'w') as f:
            f.write("DUMMY_DATA")
        return filename

    def symphony_compose(self, details):
        time.sleep(2)
        filename = f"assets/audio/track_{int(time.time())}.wav"
        with open(filename, 'w') as f:
            f.write("DUMMY_AUDIO")
        return filename

# --- 4. ENHANCED GUI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class EnhancedVibeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Enhanced Logic Init
        self.brain = EnhancedDirectorBrain()
        self.bridge = EnhancedUnrealBridge()
        self.workers = EnhancedWorkers(CPP_AI_API_URL)
        
        # State tracking
        self.last_code_id = None
        self.last_error_id = None
        self.iteration_count = 0

        # Window Setup
        self.title("Unreal AI Architect | C++ AI Platform Edition")
        self.geometry("1400x900")
        
        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_ui()
        self.check_connection()
        
        # Status indicators
        self.api_connected = False
        self.check_api_connection()

    def setup_ui(self):
        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(3, weight=1)

        self.logo = ctk.CTkLabel(
            self.sidebar,
            text="C++ AI ARCHITECT",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.logo.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Connection status frame
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.unreal_status = ctk.CTkLabel(
            self.status_frame,
            text="🔴 UNREAL OFFLINE",
            text_color="red"
        )
        self.unreal_status.pack(pady=2)
        
        self.api_status = ctk.CTkLabel(
            self.status_frame,
            text="🔴 C++ AI API OFFLINE",
            text_color="red"
        )
        self.api_status.pack(pady=2)

        # Session Info
        self.session_info = ctk.CTkFrame(self.sidebar)
        self.session_info.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            self.session_info,
            text="Session Stats",
            font=ctk.CTkFont(weight="bold")
        ).pack(pady=(10, 5))
        
        self.stats_labels = {}
        for key in ["Generated", "Errors Fixed", "Iteration"]:
            frame = ctk.CTkFrame(self.session_info, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(frame, text=f"{key}:", width=100, anchor="w").pack(side="left")
            label = ctk.CTkLabel(frame, text="0", text_color="#06b6d4")
            label.pack(side="right")
            self.stats_labels[key] = label

        # Log Box
        self.log_box = ctk.CTkTextbox(
            self.sidebar,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_box.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.log_box.configure(state="disabled")

        # --- MAIN AREA ---
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="#101010")
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        # Enhanced Tools Grid
        self.tools_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.tools_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        # Enhanced tool cards
        self.create_card(self.tools_frame, "ARCHITECT PRO", "C++ + Validation", 0, "#9333ea")
        self.create_card(self.tools_frame, "ERROR DOCTOR", "AI Debug", 1, "#ef4444")
        self.create_card(self.tools_frame, "BUILD MASTER", "Build Files", 2, "#2563eb")
        self.create_card(self.tools_frame, "GENESIS", "3D Gen", 3, "#10b981")
        self.create_card(self.tools_frame, "SYMPHONY", "Audio", 4, "#db2777")

        # Code Viewer / Viewport
        self.viewport_notebook = ctk.CTkTabview(self.main_area)
        self.viewport_notebook.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Viewport Tab
        self.viewport_tab = self.viewport_notebook.add("Viewport")
        viewport_frame = ctk.CTkFrame(self.viewport_tab, fg_color="black", border_width=2, border_color="#333")
        viewport_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(
            viewport_frame,
            text="PRISM VIEWPORT [NO SIGNAL]",
            font=ctk.CTkFont(size=24)
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        # Code Viewer Tab
        self.code_tab = self.viewport_notebook.add("Generated Code")
        self.code_viewer = ctk.CTkTextbox(
            self.code_tab,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none"
        )
        self.code_viewer.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Validation Tab
        self.validation_tab = self.viewport_notebook.add("Validation")
        self.validation_viewer = ctk.CTkTextbox(
            self.validation_tab,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.validation_viewer.pack(fill="both", expand=True, padx=10, pady=10)

        # Input Bar with Mode Selector
        self.input_frame = ctk.CTkFrame(self.main_area, fg_color="#202020", height=100)
        self.input_frame.grid(row=2, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # Mode selector
        self.mode_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.mode_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="w")
        
        ctk.CTkLabel(self.mode_frame, text="Mode:", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        self.mode_var = ctk.StringVar(value="generate")
        
        modes = [
            ("Generate", "generate"),
            ("Debug Error", "debug"),
            ("Refine", "refine"),
            ("Build Files", "build")
        ]
        
        for text, mode in modes:
            ctk.CTkRadioButton(
                self.mode_frame,
                text=text,
                variable=self.mode_var,
                value=mode,
                font=ctk.CTkFont(size=11)
            ).pack(side="left", padx=5)

        # Input entry
        self.entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Describe what you want to create or fix...",
            height=50,
            font=ctk.CTkFont(size=14)
        )
        self.entry.grid(row=1, column=0, padx=20, pady=15, sticky="ew")
        self.entry.bind("<Return>", self.submit)

        # Execute button
        self.btn = ctk.CTkButton(
            self.input_frame,
            text="EXECUTE",
            width=120,
            height=50,
            command=lambda: self.submit(None),
            fg_color="#06b6d4",
            text_color="black",
            font=ctk.CTkFont(weight="bold")
        )
        self.btn.grid(row=1, column=1, padx=(0, 20), pady=15)

    def create_card(self, parent, title, sub, col, color):
        card = ctk.CTkFrame(parent, fg_color="#1f2937")
        card.grid(row=0, column=col, padx=5, sticky="ew")
        parent.grid_columnconfigure(col, weight=1)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(weight="bold", size=11)).pack(pady=(10,0))
        ctk.CTkLabel(card, text=sub, text_color="gray", font=ctk.CTkFont(size=9)).pack(pady=(0,10))
        ctk.CTkFrame(card, height=4, fg_color=color).pack(fill="x", side="bottom")

    def log(self, sender, msg, color=None):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        
        if color:
            self.log_box.insert("end", f"[{now}] ", "timestamp")
            self.log_box.insert("end", f"{sender}: ", "sender")
            self.log_box.insert("end", f"{msg}\n", color)
        else:
            self.log_box.insert("end", f"[{now}] {sender}: {msg}\n")
        
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        
        # Configure tags for colors
        self.log_box.tag_config("success", foreground="#22c55e")
        self.log_box.tag_config("error", foreground="#ef4444")
        self.log_box.tag_config("warning", foreground="#f59e0b")
        self.log_box.tag_config("info", foreground="#06b6d4")

    def update_stat(self, key, value):
        """Update session statistics"""
        if key in self.stats_labels:
            self.stats_labels[key].configure(text=str(value))

    def check_connection(self):
        if self.bridge.send_command("PING", {}):
            self.unreal_status.configure(text="🟢 UNREAL ONLINE", text_color="#22c55e")
        else:
            self.unreal_status.configure(text="🔴 UNREAL OFFLINE", text_color="#ef4444")
        self.after(5000, self.check_connection)
    
    def check_api_connection(self):
        """Check C++ AI Platform API connection"""
        def check():
            try:
                import requests
                response = requests.get(f"{CPP_AI_API_URL.replace('/api', '')}/health", timeout=2)
                if response.status_code == 200:
                    self.api_connected = True
                    self.after(0, lambda: self.api_status.configure(
                        text="🟢 C++ AI API ONLINE",
                        text_color="#22c55e"
                    ))
                else:
                    raise Exception("API not responding")
            except:
                self.api_connected = False
                self.after(0, lambda: self.api_status.configure(
                    text="🔴 C++ AI API OFFLINE",
                    text_color="#ef4444"
                ))
        
        threading.Thread(target=check, daemon=True).start()
        self.after(10000, self.check_api_connection)

    def submit(self, event):
        prompt = self.entry.get()
        if not prompt:
            return
            
        mode = self.mode_var.get()
        self.entry.delete(0, "end")
        self.log("USER", f"[{mode.upper()}] {prompt}", "info")
        
        # Process based on mode
        threading.Thread(
            target=self.process_with_mode,
            args=(prompt, mode),
            daemon=True
        ).start()

    def process_with_mode(self, prompt, mode):
        """Process command based on selected mode"""
        
        if mode == "generate":
            self.process_generate(prompt)
        elif mode == "debug":
            self.process_debug(prompt)
        elif mode == "refine":
            self.process_refine(prompt)
        elif mode == "build":
            self.process_build(prompt)

    def process_generate(self, prompt):
        """Generate new C++ code"""
        self.log("ARCHITECT PRO", "Generating code with AI validation...", "info")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.workers.architect_pro_generate(
                    prompt,
                    {
                        "validation": True,
                        "build_files": True,
                        "error_check": True,
                        "optimization": True
                    }
                )
            )
            
            if "error" in result:
                self.log("ERROR", result["error"], "error")
                return
            
            # Display generated code
            self.display_code(result)
            
            # Display validation
            self.display_validation(result)
            
            # Update stats
            self.last_code_id = result.get("code_id")
            current = int(self.stats_labels["Generated"].cget("text"))
            self.update_stat("Generated", current + 1)
            
            # Log success
            quality = result.get("quality_score", 0)
            self.log(
                "ARCHITECT PRO",
                f"Code generated! Quality: {quality}% | File: {result.get('cpp_file')}",
                "success" if quality > 80 else "warning"
            )
            
            if result.get("requires_review"):
                self.log("WARNING", "⚠️ Manual review required before production use", "warning")
            
            # Import to Unreal if connected
            if self.bridge.connected:
                self.bridge.import_cpp_code(result.get("cpp_file"), "GeneratedModule")
                self.log("BRIDGE", "Code imported to Unreal Engine", "success")
                
        except Exception as e:
            self.log("ERROR", f"Generation failed: {str(e)}", "error")
        finally:
            loop.close()

    def process_debug(self, error_message):
        """Debug and fix errors"""
        self.log("ERROR DOCTOR", "Analyzing error with AI...", "info")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.workers.error_doctor_analyze(error_message)
            )
            
            if "error" in result:
                self.log("ERROR", result["error"], "error")
                return
            
            # Display analysis
            self.display_error_analysis(result)
            
            # Check if auto-fix was applied
            if "auto_fix" in result and result["auto_fix"].get("success"):
                self.log(
                    "ERROR DOCTOR",
                    f"✓ Error fixed automatically! File: {result['auto_fix'].get('saved_to')}",
                    "success"
                )
                current = int(self.stats_labels["Errors Fixed"].cget("text"))
                self.update_stat("Errors Fixed", current + 1)
            else:
                self.log(
                    "ERROR DOCTOR",
                    f"Analysis complete. Severity: {result.get('severity')} | Confidence: {result.get('confidence_score', 0)*100:.0f}%",
                    "warning"
                )
            
            self.last_error_id = result.get("error_id")
            
        except Exception as e:
            self.log("ERROR", f"Debug failed: {str(e)}", "error")
        finally:
            loop.close()

    def process_refine(self, feedback):
        """Refine existing code"""
        if not self.last_code_id:
            self.log("WARNING", "No code to refine. Generate code first.", "warning")
            return
        
        self.log("ARCHITECT PRO", f"Refining code (Iteration {self.iteration_count + 1})...", "info")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.workers.refine_code(self.last_code_id, feedback)
            )
            
            if "error" in result:
                self.log("ERROR", result["error"], "error")
                return
            
            self.iteration_count += 1
            self.update_stat("Iteration", self.iteration_count)
            
            self.log(
                "ARCHITECT PRO",
                f"Code refined! Improvements: {len(result.get('improvements', []))}",
                "success"
            )
            
            # Update last_code_id to new refined version
            if "refined_code" in result:
                self.last_code_id = result["refined_code"].get("id")
            
        except Exception as e:
            self.log("ERROR", f"Refinement failed: {str(e)}", "error")
        finally:
            loop.close()

    def process_build(self, prompt):
        """Generate build files"""
        if not self.last_code_id:
            self.log("WARNING", "No code to build. Generate code first.", "warning")
            return
        
        self.log("BUILD MASTER", "Generating build files...", "info")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.workers.generate_build_files(self.last_code_id)
            )
            
            if "error" in result:
                self.log("ERROR", result["error"], "error")
                return
            
            # Display instructions
            self.display_build_instructions(result)
            
            self.log(
                "BUILD MASTER",
                f"Build files generated: {', '.join(result.get('files', {}).keys())}",
                "success"
            )
            
            # Import to Unreal if connected
            if self.bridge.connected:
                for file_path in result.get("files", {}).values():
                    self.bridge.import_build_files(file_path)
                self.log("BRIDGE", "Build files imported to Unreal", "success")
            
        except Exception as e:
            self.log("ERROR", f"Build file generation failed: {str(e)}", "error")
        finally:
            loop.close()

    def display_code(self, result):
        """Display generated code in code viewer"""
        self.code_viewer.delete("1.0", "end")
        
        with open(result.get("cpp_file", ""), 'r') as f:
            code = f.read()
            self.code_viewer.insert("1.0", code)
        
        self.viewport_notebook.set("Generated Code")

    def display_validation(self, result):
        """Display validation results"""
        self.validation_viewer.delete("1.0", "end")
        
        validation = result.get("validation", {})
        quality_score = result.get("quality_score", 0)
        
        output = f"CODE VALIDATION REPORT\n"
        output += "=" * 50 + "\n\n"
        output += f"Quality Score: {quality_score}%\n"
        output += f"Requires Review: {result.get('requires_review', True)}\n\n"
        
        if validation.get("issues"):
            output += "CRITICAL ISSUES:\n"
            for issue in validation["issues"]:
                output += f"  ❌ {issue}\n"
            output += "\n"
        
        if validation.get("warnings"):
            output += "WARNINGS:\n"
            for warning in validation["warnings"]:
                output += f"  ⚠️  {warning}\n"
            output += "\n"
        
        if validation.get("suggestions"):
            output += "SUGGESTIONS:\n"
            for suggestion in validation["suggestions"]:
                output += f"  💡 {suggestion}\n"
        
        self.validation_viewer.insert("1.0", output)

    def display_error_analysis(self, result):
        """Display error analysis"""
        self.validation_viewer.delete("1.0", "end")
        
        output = f"ERROR ANALYSIS REPORT\n"
        output += "=" * 50 + "\n\n"
        output += f"Severity: {result.get('severity', 'N/A').upper()}\n"
        output += f"Category: {result.get('category', 'N/A')}\n"
        output += f"Confidence: {result.get('confidence_score', 0)*100:.0f}%\n\n"
        output += f"Summary: {result.get('summary', 'N/A')}\n\n"
        output += f"Root Cause:\n{result.get('root_cause', 'N/A')}\n\n"
        output += f"Explanation:\n{result.get('explanation', 'N/A')}\n\n"
        
        if result.get("suggested_fixes"):
            output += "SUGGESTED FIXES:\n"
            for i, fix in enumerate(result["suggested_fixes"], 1):
                output += f"\n{i}. {fix.get('description', 'N/A')}\n"
                output += f"   Confidence: {fix.get('confidence', 0)*100:.0f}%\n"
                output += f"   Risk: {fix.get('risk_level', 'N/A')}\n"
        
        self.validation_viewer.insert("1.0", output)
        self.viewport_notebook.set("Validation")

    def display_build_instructions(self, result):
        """Display build instructions"""
        self.validation_viewer.delete("1.0", "end")
        
        output = "BUILD FILES GENERATED\n"
        output += "=" * 50 + "\n\n"
        
        for filename, filepath in result.get("files", {}).items():
            output += f"📄 {filename}\n"
            output += f"   Location: {filepath}\n\n"
        
        output += "\nINSTRUCTIONS:\n"
        output += result.get("instructions", "No instructions available")
        
        self.validation_viewer.insert("1.0", output)
        self.viewport_notebook.set("Validation")

if __name__ == "__main__":
    # Check if API keys are set
    if not OPENAI_API_KEY:
        print("⚠️  WARNING: OPENAI_API_KEY not set in .env file")
        print("   Some features may not work correctly.")
    
    app = EnhancedVibeApp()
    app.mainloop()
