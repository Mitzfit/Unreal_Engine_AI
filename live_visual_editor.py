"""
Live Visual Editor - Real-time Preview and Tweaking Window
Allows users to see and modify code/assets as they're being created
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from PIL import Image, ImageTk
import os

@dataclass
class AssetPreview:
    """Preview data for an asset"""
    asset_type: str
    name: str
    thumbnail_path: Optional[str] = None
    properties: Dict[str, Any] = None
    meshes: List[str] = None
    materials: List[str] = None

class LiveVisualEditor(ctk.CTkToplevel):
    """
    Separate window for live editing and preview
    Shows real-time updates as code/assets are generated
    """
    
    def __init__(self, parent, title="Live Editor - Unreal AI Architect"):
        super().__init__(parent)
        
        self.title(title)
        self.geometry("1600x1000")
        
        # State
        self.current_asset = None
        self.current_code = ""
        self.is_generating = False
        self.preview_mode = "3D"  # 3D, Code, Both
        self.on_property_change = None
        self.on_code_change = None
        
        # Grid configuration
        self.grid_columnconfigure(0, weight=0)  # Left panel
        self.grid_columnconfigure(1, weight=1)  # Center viewport
        self.grid_columnconfigure(2, weight=0)  # Right panel
        self.grid_rowconfigure(0, weight=1)
        
        self.setup_ui()
        
        # Auto-refresh timer
        self.after(100, self.update_preview)
    
    def setup_ui(self):
        """Setup the three-panel editor interface"""
        
        # ===== LEFT PANEL: Properties & Hierarchy =====
        self.left_panel = ctk.CTkFrame(self, width=300)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=10)
        self.left_panel.grid_propagate(False)
        
        self.setup_left_panel()
        
        # ===== CENTER: 3D Viewport / Code Preview =====
        self.center_panel = ctk.CTkFrame(self)
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        self.center_panel.grid_rowconfigure(1, weight=1)
        self.center_panel.grid_columnconfigure(0, weight=1)
        
        self.setup_center_panel()
        
        # ===== RIGHT PANEL: Code Editor & Details =====
        self.right_panel = ctk.CTkFrame(self, width=500)
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=(5,10), pady=10)
        self.right_panel.grid_propagate(False)
        
        self.setup_right_panel()
    
    def setup_left_panel(self):
        """Setup left panel with hierarchy and properties"""
        
        # Header
        ctk.CTkLabel(
            self.left_panel,
            text="⚙️ PROPERTIES",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Hierarchy Tree
        hierarchy_frame = ctk.CTkFrame(self.left_panel)
        hierarchy_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        
        ctk.CTkLabel(
            hierarchy_frame,
            text="Scene Hierarchy",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=5)
        
        # Use tkinter Treeview for hierarchy
        tree_container = ctk.CTkFrame(hierarchy_frame)
        tree_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.hierarchy_tree = ttk.Treeview(tree_container, style="Custom.Treeview")
        self.hierarchy_tree.pack(fill="both", expand=True)
        
        # Configure treeview style
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b")
        
        # Scrollable Properties
        self.properties_frame = ctk.CTkScrollableFrame(
            self.left_panel,
            label_text="Asset Properties"
        )
        self.properties_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        
        self.property_widgets = {}
    
    def setup_center_panel(self):
        """Setup center viewport panel"""
        
        # Toolbar
        toolbar = ctk.CTkFrame(self.center_panel, height=50)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        toolbar.grid_columnconfigure(1, weight=1)
        
        # View mode selector
        self.view_mode = ctk.CTkSegmentedButton(
            toolbar,
            values=["3D Viewport", "Code View", "Split View"],
            command=self.change_view_mode
        )
        self.view_mode.set("3D Viewport")
        self.view_mode.pack(side="left", padx=10, pady=10)
        
        # Playback controls
        control_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        control_frame.pack(side="right", padx=10)
        
        ctk.CTkButton(
            control_frame,
            text="▶ Play",
            width=80,
            command=self.play_preview,
            fg_color="#22c55e"
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            control_frame,
            text="⏸ Pause",
            width=80,
            command=self.pause_preview
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            control_frame,
            text="⏹ Stop",
            width=80,
            command=self.stop_preview
        ).pack(side="left", padx=2)
        
        # Main viewport container
        self.viewport_container = ctk.CTkFrame(self.center_panel, fg_color="black")
        self.viewport_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.viewport_container.grid_rowconfigure(0, weight=1)
        self.viewport_container.grid_columnconfigure(0, weight=1)
        
        # 3D Viewport
        self.viewport_3d = ctk.CTkFrame(self.viewport_container, fg_color="black")
        self.viewport_3d.grid(row=0, column=0, sticky="nsew")
        
        self.viewport_label = ctk.CTkLabel(
            self.viewport_3d,
            text="🎮 3D PREVIEW\n\n[Asset will appear here]\n\nGenerating...",
            font=ctk.CTkFont(size=18),
            text_color="gray"
        )
        self.viewport_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Code viewport (hidden initially)
        self.viewport_code = ctk.CTkTextbox(
            self.viewport_container,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none"
        )
        self.viewport_code.grid(row=0, column=0, sticky="nsew")
        self.viewport_code.grid_remove()
        
        # Generation progress
        self.progress_frame = ctk.CTkFrame(self.center_panel, height=40)
        self.progress_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Ready")
        self.progress_label.pack(side="left", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)
        self.progress_bar.set(0)
    
    def setup_right_panel(self):
        """Setup right panel with code editor and details"""
        
        # Header with tabs
        ctk.CTkLabel(
            self.right_panel,
            text="📝 CODE & DETAILS",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Tab view
        self.right_tabs = ctk.CTkTabview(self.right_panel)
        self.right_tabs.pack(fill="both", expand=True, padx=10, pady=(0,10))
        
        # Code Editor Tab
        self.code_tab = self.right_tabs.add("Code")
        self.setup_code_editor_tab()
        
        # Materials Tab
        self.materials_tab = self.right_tabs.add("Materials")
        self.setup_materials_tab()
        
        # Physics Tab
        self.physics_tab = self.right_tabs.add("Physics")
        self.setup_physics_tab()
        
        # AI Assistant Tab
        self.assistant_tab = self.right_tabs.add("AI Chat")
        self.setup_assistant_tab()
    
    def setup_code_editor_tab(self):
        """Setup code editor in right panel"""
        
        # Code language selector
        lang_frame = ctk.CTkFrame(self.code_tab, fg_color="transparent")
        lang_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(lang_frame, text="Language:").pack(side="left", padx=5)
        
        self.code_language = ctk.CTkSegmentedButton(
            lang_frame,
            values=["C++ Header", "C++ Source", "Blueprint"],
            command=self.switch_code_view
        )
        self.code_language.set("C++ Header")
        self.code_language.pack(side="left", padx=5)
        
        # Code editor
        self.code_editor = ctk.CTkTextbox(
            self.code_tab,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="none"
        )
        self.code_editor.pack(fill="both", expand=True, pady=10)
        self.code_editor.bind("<KeyRelease>", self.on_code_edited)
        
        # Code actions
        actions_frame = ctk.CTkFrame(self.code_tab, fg_color="transparent")
        actions_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(
            actions_frame,
            text="💾 Save",
            width=100,
            command=self.save_code
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            actions_frame,
            text="🔄 Refresh",
            width=100,
            command=self.refresh_code
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            actions_frame,
            text="✨ Format",
            width=100,
            command=self.format_code
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            actions_frame,
            text="🔍 Analyze",
            width=100,
            command=self.analyze_code,
            fg_color="#06b6d4"
        ).pack(side="left", padx=2)
    
    def setup_materials_tab(self):
        """Setup materials editor"""
        
        ctk.CTkLabel(
            self.materials_tab,
            text="Material Editor",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)
        
        # Material list
        self.materials_list = ctk.CTkScrollableFrame(self.materials_tab)
        self.materials_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add material button
        ctk.CTkButton(
            self.materials_tab,
            text="➕ Add Material",
            command=self.add_material
        ).pack(pady=10)
    
    def setup_physics_tab(self):
        """Setup physics properties"""
        
        ctk.CTkLabel(
            self.physics_tab,
            text="Physics Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)
        
        # Physics toggles
        physics_frame = ctk.CTkFrame(self.physics_tab)
        physics_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.physics_enabled = ctk.CTkSwitch(
            physics_frame,
            text="Enable Physics Simulation",
            command=self.toggle_physics
        )
        self.physics_enabled.pack(pady=10)
        
        self.gravity_enabled = ctk.CTkSwitch(
            physics_frame,
            text="Enable Gravity"
        )
        self.gravity_enabled.pack(pady=10)
        
        # Mass slider
        ctk.CTkLabel(physics_frame, text="Mass (kg):").pack(pady=(20,5))
        self.mass_slider = ctk.CTkSlider(
            physics_frame,
            from_=0.1,
            to=1000,
            command=self.update_mass
        )
        self.mass_slider.set(100)
        self.mass_slider.pack(fill="x", padx=20, pady=5)
        
        self.mass_label = ctk.CTkLabel(physics_frame, text="100 kg")
        self.mass_label.pack()
    
    def setup_assistant_tab(self):
        """Setup AI assistant chat in tab"""
        
        # Chat history
        self.chat_history = ctk.CTkTextbox(
            self.assistant_tab,
            font=ctk.CTkFont(size=11),
            state="disabled"
        )
        self.chat_history.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Quick actions
        quick_frame = ctk.CTkFrame(self.assistant_tab, fg_color="transparent")
        quick_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(quick_frame, text="Quick Actions:").pack(anchor="w", pady=2)
        
        quick_actions = [
            ("Add animation", "add animation"),
            ("Improve performance", "optimize code"),
            ("Add collision", "add collision mesh"),
            ("Export asset", "export to file")
        ]
        
        for label, command in quick_actions:
            ctk.CTkButton(
                quick_frame,
                text=label,
                width=120,
                height=28,
                command=lambda cmd=command: self.quick_action(cmd)
            ).pack(side="left", padx=2, pady=2)
        
        # Chat input
        input_frame = ctk.CTkFrame(self.assistant_tab)
        input_frame.pack(fill="x", padx=5, pady=5)
        
        self.chat_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Ask AI to modify this asset..."
        )
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.chat_input.bind("<Return>", lambda e: self.send_chat_message())
        
        ctk.CTkButton(
            input_frame,
            text="Send",
            width=80,
            command=self.send_chat_message
        ).pack(side="right")
    
    # ===== PROPERTY MANAGEMENT =====
    
    def load_asset_properties(self, asset_data: Dict[str, Any]):
        """Load asset properties into the properties panel"""
        
        # Clear existing
        for widget in self.property_widgets.values():
            widget.destroy()
        self.property_widgets.clear()
        
        # Add new properties
        properties = asset_data.get("properties", {})
        
        for prop_name, prop_value in properties.items():
            self.add_property_widget(prop_name, prop_value)
        
        # Update hierarchy
        self.update_hierarchy(asset_data)
    
    def add_property_widget(self, name: str, value: Any):
        """Add a property widget to the properties panel"""
        
        frame = ctk.CTkFrame(self.properties_frame, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        label = ctk.CTkLabel(frame, text=f"{name}:", width=120, anchor="w")
        label.pack(side="left", padx=5)
        
        if isinstance(value, bool):
            widget = ctk.CTkSwitch(frame, text="")
            if value:
                widget.select()
            widget.configure(command=lambda: self.property_changed(name, widget.get()))
        elif isinstance(value, (int, float)):
            widget = ctk.CTkEntry(frame, width=100)
            widget.insert(0, str(value))
            widget.bind("<FocusOut>", lambda e: self.property_changed(name, widget.get()))
        elif isinstance(value, str):
            widget = ctk.CTkEntry(frame)
            widget.insert(0, value)
            widget.bind("<FocusOut>", lambda e: self.property_changed(name, widget.get()))
        else:
            widget = ctk.CTkLabel(frame, text=str(value))
        
        widget.pack(side="left", fill="x", expand=True, padx=5)
        self.property_widgets[name] = widget
    
    def property_changed(self, name: str, value: Any):
        """Handle property value change"""
        print(f"Property changed: {name} = {value}")
        if self.on_property_change:
            self.on_property_change(name, value)
        
        # Trigger preview update
        self.update_preview()
    
    def update_hierarchy(self, asset_data: Dict[str, Any]):
        """Update the scene hierarchy tree"""
        
        # Clear existing
        for item in self.hierarchy_tree.get_children():
            self.hierarchy_tree.delete(item)
        
        # Add root
        asset_name = asset_data.get("name", "Asset")
        root = self.hierarchy_tree.insert("", "end", text=asset_name, open=True)
        
        # Add components
        components = asset_data.get("components", [])
        for comp in components:
            self.hierarchy_tree.insert(root, "end", text=comp)
        
        # Add meshes
        meshes = asset_data.get("meshes", [])
        if meshes:
            mesh_parent = self.hierarchy_tree.insert(root, "end", text="Meshes", open=True)
            for mesh in meshes:
                self.hierarchy_tree.insert(mesh_parent, "end", text=mesh)
    
    # ===== VIEW CONTROL =====
    
    def change_view_mode(self, value: str):
        """Change viewport display mode"""
        
        if value == "3D Viewport":
            self.viewport_3d.grid()
            self.viewport_code.grid_remove()
        elif value == "Code View":
            self.viewport_3d.grid_remove()
            self.viewport_code.grid()
        elif value == "Split View":
            # Implement split view
            self.viewport_3d.grid()
            self.viewport_code.grid()
    
    def play_preview(self):
        """Play animation/simulation in viewport"""
        self.viewport_label.configure(text="▶ Playing...")
    
    def pause_preview(self):
        """Pause animation/simulation"""
        self.viewport_label.configure(text="⏸ Paused")
    
    def stop_preview(self):
        """Stop animation/simulation"""
        self.viewport_label.configure(text="⏹ Stopped")
    
    def update_preview(self):
        """Update the preview display"""
        
        if self.is_generating:
            # Show generation animation
            current_text = self.viewport_label.cget("text")
            dots = current_text.count(".")
            new_dots = "." * ((dots + 1) % 4)
            self.viewport_label.configure(text=f"Generating{new_dots}")
        
        # Schedule next update
        self.after(100, self.update_preview)
    
    # ===== CODE MANAGEMENT =====
    
    def update_code_display(self, code: str, language: str = "cpp"):
        """Update the code display with new code"""
        
        self.current_code = code
        self.code_editor.delete("1.0", "end")
        self.code_editor.insert("1.0", code)
        
        # Also update viewport code view
        self.viewport_code.delete("1.0", "end")
        self.viewport_code.insert("1.0", code)
    
    def on_code_edited(self, event):
        """Handle code editing by user"""
        new_code = self.code_editor.get("1.0", "end-1c")
        
        if new_code != self.current_code:
            self.current_code = new_code
            if self.on_code_change:
                self.on_code_change(new_code)
    
    def save_code(self):
        """Save current code to file"""
        code = self.code_editor.get("1.0", "end-1c")
        
        filename = f"assets/code_generated/LiveEdited_{int(time.time())}.cpp"
        with open(filename, 'w') as f:
            f.write(code)
        
        self.add_chat_message("System", f"Code saved to {filename}")
    
    def refresh_code(self):
        """Refresh code from source"""
        self.add_chat_message("System", "Code refreshed from generator")
    
    def format_code(self):
        """Auto-format the code"""
        self.add_chat_message("System", "Code formatted (simulated)")
    
    def analyze_code(self):
        """Analyze code for errors"""
        self.add_chat_message("System", "Code analysis started...")
    
    def switch_code_view(self, value: str):
        """Switch between header/source/blueprint"""
        self.add_chat_message("System", f"Switched to {value} view")
    
    # ===== MATERIALS =====
    
    def add_material(self):
        """Add a new material slot"""
        
        mat_frame = ctk.CTkFrame(self.materials_list)
        mat_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(mat_frame, text="Material Slot").pack(side="left", padx=5)
        
        color_btn = ctk.CTkButton(
            mat_frame,
            text="Pick Color",
            width=100,
            command=lambda: self.pick_material_color(mat_frame)
        )
        color_btn.pack(side="right", padx=5)
    
    def pick_material_color(self, mat_frame):
        """Open color picker for material"""
        self.add_chat_message("System", "Material color picker (simulated)")
    
    # ===== PHYSICS =====
    
    def toggle_physics(self):
        """Toggle physics simulation"""
        enabled = self.physics_enabled.get()
        self.add_chat_message("System", f"Physics {'enabled' if enabled else 'disabled'}")
    
    def update_mass(self, value):
        """Update mass property"""
        self.mass_label.configure(text=f"{int(value)} kg")
    
    # ===== AI CHAT =====
    
    def add_chat_message(self, sender: str, message: str):
        """Add message to chat history"""
        
        self.chat_history.configure(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.chat_history.insert("end", f"[{timestamp}] {sender}: {message}\n")
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")
    
    def send_chat_message(self):
        """Send user message to AI"""
        
        message = self.chat_input.get()
        if not message.strip():
            return
        
        self.add_chat_message("You", message)
        self.chat_input.delete(0, "end")
        
        # Simulate AI response
        self.after(500, lambda: self.add_chat_message(
            "AI",
            "I understand you want to modify the asset. Processing your request..."
        ))
    
    def quick_action(self, action: str):
        """Execute a quick action"""
        self.chat_input.delete(0, "end")
        self.chat_input.insert(0, action)
        self.send_chat_message()
    
    # ===== PUBLIC API =====
    
    def set_generating(self, generating: bool, progress: float = 0.0):
        """Set generation state"""
        
        self.is_generating = generating
        self.progress_bar.set(progress)
        
        if generating:
            self.progress_label.configure(text=f"Generating... {int(progress*100)}%")
        else:
            self.progress_label.configure(text="Complete")
    
    def load_asset(self, asset_data: Dict[str, Any]):
        """Load asset data into editor"""
        
        self.current_asset = asset_data
        self.load_asset_properties(asset_data)
        
        # Update viewport
        asset_type = asset_data.get("asset_type", "Unknown")
        asset_name = asset_data.get("name", "Asset")
        
        self.viewport_label.configure(
            text=f"✓ {asset_type.upper()}\n\n{asset_name}\n\nReady for editing"
        )
        
        self.add_chat_message("System", f"Loaded {asset_name} ({asset_type})")
    
    def set_property_change_callback(self, callback: Callable):
        """Set callback for property changes"""
        self.on_property_change = callback
    
    def set_code_change_callback(self, callback: Callable):
        """Set callback for code changes"""
        self.on_code_change = callback