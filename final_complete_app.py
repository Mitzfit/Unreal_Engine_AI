"""
FINAL COMPLETE SYSTEM
Image Upload → AI Analysis → 3D Generation → Game Environment → Playable Demo
"""

import time
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import threading
import asyncio
import os
from datetime import datetime

# Import all systems
import sys
sys.path.append(os.path.dirname(__file__))

from image_to_game_converter import ImageToGameConverter, AIVisionSystem
from game_environment_builder import GameEnvironmentBuilder
from complete_ultimate_system import CompleteUltimateApp
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CPP_AI_API_URL = os.getenv("CPP_AI_API_URL", "http://localhost:8000/api")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class ImageUploadCanvas(ctk.CTkFrame):
    """
    Interactive canvas for drawing and image upload
    """
    
    def __init__(self, parent, on_submit_callback):
        super().__init__(parent)
        
        self.on_submit = on_submit_callback
        self.current_image = None
        self.image_path = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        ctk.CTkLabel(
            self,
            text="📸 Upload or Draw Your Idea",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        # Canvas for drawing/displaying
        self.canvas_frame = ctk.CTkFrame(self, width=600, height=400, fg_color="white")
        self.canvas_frame.pack(pady=10, padx=20)
        self.canvas_frame.pack_propagate(False)
        
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=600,
            height=400,
            bg="white",
            cursor="cross"
        )
        self.canvas.pack()
        
        # Drawing state
        self.drawing = False
        self.last_x = None
        self.last_y = None
        self.draw_color = "black"
        self.draw_width = 3
        
        # Bind drawing events
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        
        # Create PIL image for drawing
        self.pil_image = Image.new("RGB", (600, 400), "white")
        self.pil_draw = ImageDraw.Draw(self.pil_image)
        
        # Controls
        controls_frame = ctk.CTkFrame(self)
        controls_frame.pack(fill="x", padx=20, pady=10)
        
        # Upload button
        ctk.CTkButton(
            controls_frame,
            text="📁 Upload Image",
            command=self.upload_image,
            width=150,
            height=40
        ).pack(side="left", padx=5)
        
        # Clear button
        ctk.CTkButton(
            controls_frame,
            text="🗑️ Clear",
            command=self.clear_canvas,
            width=100,
            height=40,
            fg_color="#ef4444"
        ).pack(side="left", padx=5)
        
        # Color picker
        ctk.CTkLabel(controls_frame, text="Color:").pack(side="left", padx=5)
        
        colors = ["black", "red", "blue", "green", "yellow", "orange", "purple"]
        for color in colors:
            btn = tk.Button(
                controls_frame,
                bg=color,
                width=3,
                height=1,
                command=lambda c=color: self.set_color(c)
            )
            btn.pack(side="left", padx=2)
        
        # Brush size
        ctk.CTkLabel(controls_frame, text="Size:").pack(side="left", padx=(20,5))
        
        self.brush_slider = ctk.CTkSlider(
            controls_frame,
            from_=1,
            to=10,
            width=100,
            command=self.set_brush_size
        )
        self.brush_slider.set(3)
        self.brush_slider.pack(side="left", padx=5)
        
        # Description
        desc_frame = ctk.CTkFrame(self)
        desc_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            desc_frame,
            text="Describe what you want to create:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=10, pady=5)
        
        self.description_entry = ctk.CTkEntry(
            desc_frame,
            placeholder_text="E.g., 'A medieval knight character for my RPG game'",
            height=40
        )
        self.description_entry.pack(fill="x", padx=10, pady=5)
        
        # Submit button
        self.submit_btn = ctk.CTkButton(
            self,
            text="✨ Generate from Image",
            command=self.submit_image,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#06b6d4",
            text_color="black"
        )
        self.submit_btn.pack(pady=20, padx=20, fill="x")
    
    def start_draw(self, event):
        self.drawing = True
        self.last_x = event.x
        self.last_y = event.y
    
    def draw(self, event):
        if self.drawing:
            x, y = event.x, event.y
            self.canvas.create_line(
                self.last_x, self.last_y, x, y,
                fill=self.draw_color,
                width=self.draw_width,
                capstyle=tk.ROUND,
                smooth=True
            )
            self.pil_draw.line(
                [self.last_x, self.last_y, x, y],
                fill=self.draw_color,
                width=self.draw_width
            )
            self.last_x = x
            self.last_y = y
    
    def stop_draw(self, event):
        self.drawing = False
    
    def set_color(self, color):
        self.draw_color = color
    
    def set_brush_size(self, value):
        self.draw_width = int(value)
    
    def clear_canvas(self):
        self.canvas.delete("all")
        self.pil_image = Image.new("RGB", (600, 400), "white")
        self.pil_draw = ImageDraw.Draw(self.pil_image)
        self.current_image = None
        self.image_path = None
    
    def upload_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, file_path):
        # Load and display image
        img = Image.open(file_path)
        
        # Resize to fit canvas
        img.thumbnail((600, 400), Image.Resampling.LANCZOS)
        
        # Update canvas
        self.canvas.delete("all")
        self.pil_image = img.resize((600, 400))
        self.current_image = ImageTk.PhotoImage(img)
        self.canvas.create_image(300, 200, image=self.current_image)
        
        self.image_path = file_path
    
    def submit_image(self):
        # Save current canvas/image
        if not self.image_path:
            # Save drawn image
            temp_path = f"temp_drawing_{int(time.time())}.png"
            self.pil_image.save(temp_path)
            self.image_path = temp_path
        
        description = self.description_entry.get()
        
        if self.on_submit:
            self.on_submit(self.image_path, description)

class GameBuilderPanel(ctk.CTkFrame):
    """
    Interactive game environment builder panel
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.builder = GameEnvironmentBuilder()
        self.current_assets = []
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        ctk.CTkLabel(
            self,
            text="🎮 Game Environment Builder",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        # Environment info
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        self.env_label = ctk.CTkLabel(
            info_frame,
            text="No environment created",
            font=ctk.CTkFont(size=12)
        )
        self.env_label.pack(pady=5)
        
        # Create environment
        create_frame = ctk.CTkFrame(self)
        create_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(create_frame, text="Create Environment:").pack(pady=5)
        
        self.env_name_entry = ctk.CTkEntry(
            create_frame,
            placeholder_text="Environment name"
        )
        self.env_name_entry.pack(fill="x", padx=10, pady=5)
        
        self.template_var = ctk.StringVar(value="empty")
        
        template_frame = ctk.CTkFrame(create_frame, fg_color="transparent")
        template_frame.pack(pady=5)
        
        ctk.CTkLabel(template_frame, text="Template:").pack(side="left", padx=5)
        
        templates = ["empty", "fps_arena", "platformer"]
        for template in templates:
            ctk.CTkRadioButton(
                template_frame,
                text=template.replace("_", " ").title(),
                variable=self.template_var,
                value=template
            ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            create_frame,
            text="Create Environment",
            command=self.create_environment,
            fg_color="#22c55e"
        ).pack(pady=10)
        
        # Assets list
        assets_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Assets in Environment",
            height=200
        )
        assets_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.assets_list = assets_frame
        
        # Actions
        actions_frame = ctk.CTkFrame(self)
        actions_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            actions_frame,
            text="🎨 Generate Level Layout",
            command=self.generate_layout,
            width=200
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            actions_frame,
            text="▶️ Create Playable Demo",
            command=self.create_demo,
            width=200,
            fg_color="#9333ea"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            actions_frame,
            text="💾 Export to Unreal",
            command=self.export_environment,
            width=200,
            fg_color="#06b6d4"
        ).pack(side="left", padx=5)
    
    def create_environment(self):
        name = self.env_name_entry.get()
        template = self.template_var.get()
        
        if not name:
            name = f"Environment_{int(time.time())}"
        
        env = self.builder.create_environment(name, template)
        
        self.env_label.configure(
            text=f"Environment: {env.name}\nTemplate: {template}"
        )
    
    def add_generated_asset(self, asset_data: dict):
        """Add asset from image generation"""
        
        if not self.builder.current_environment:
            self.create_environment()
        
        result = self.builder.add_asset_to_environment(asset_data)
        
        if result.get("success"):
            self.current_assets.append(asset_data)
            self.update_assets_display()
    
    def update_assets_display(self):
        """Update assets list"""
        
        for widget in self.assets_list.winfo_children():
            widget.destroy()
        
        for i, asset in enumerate(self.current_assets):
            asset_frame = ctk.CTkFrame(self.assets_list)
            asset_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                asset_frame,
                text=f"{i+1}. {asset.get('asset_name', 'Asset')}",
                anchor="w"
            ).pack(side="left", padx=10)
            
            ctk.CTkButton(
                asset_frame,
                text="Remove",
                width=80,
                height=24,
                command=lambda idx=i: self.remove_asset(idx)
            ).pack(side="right", padx=5)
    
    def remove_asset(self, index):
        if 0 <= index < len(self.current_assets):
            self.current_assets.pop(index)
            self.update_assets_display()
    
    def generate_layout(self):
        """Generate level layout"""
        
        # Show layout options dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Generate Level Layout")
        dialog.geometry("400x300")
        
        ctk.CTkLabel(dialog, text="Layout Type:", font=ctk.CTkFont(size=14)).pack(pady=10)
        
        layout_var = ctk.StringVar(value="arena")
        
        layouts = ["arena", "linear", "open_world", "maze"]
        for layout in layouts:
            ctk.CTkRadioButton(
                dialog,
                text=layout.replace("_", " ").title(),
                variable=layout_var,
                value=layout
            ).pack(pady=5)
        
        def generate():
            layout_type = layout_var.get()
            layout_data = self.builder.generate_level_layout(layout_type, "medium")
            dialog.destroy()
            
            # Show success message
            ctk.CTkLabel(
                self,
                text=f"✓ Generated {layout_type} layout!",
                text_color="#22c55e"
            ).pack(pady=5)
        
        ctk.CTkButton(
            dialog,
            text="Generate",
            command=generate
        ).pack(pady=20)
    
    def create_demo(self):
        """Create playable demo"""
        
        if not self.builder.current_environment:
            return
        
        demo = self.builder.create_playable_demo(
            self.builder.current_environment,
            "walkthrough"
        )
        
        # Show demo info
        info_text = f"""Demo Created!

Environment: {self.builder.current_environment.name}
Assets: {len(self.current_assets)}
Type: Walkthrough

Controls:
- WASD: Move
- Space: Jump
- E: Interact
- Esc: Menu

The demo is ready to test!
"""
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Demo Ready")
        dialog.geometry("400x400")
        
        ctk.CTkTextbox(dialog, font=ctk.CTkFont(family="Consolas", size=11)).pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )
        
        text_widget = dialog.winfo_children()[0]
        text_widget.insert("1.0", info_text)
    
    def export_environment(self):
        """Export to Unreal"""
        
        if not self.builder.current_environment:
            return
        
        result = self.builder.export_to_unreal("exports/environments")
        
        if result.get("success"):
            message = f"""Export Successful!

Level: {result['level_path']}
Import Script: {result['import_script']}
Actors: {result['actors_count']}

To import in Unreal Engine:
1. Copy files to your project
2. Run ImportLevel.py in Unreal Editor
3. Level will be created automatically!
"""
            
            dialog = ctk.CTkToplevel(self)
            dialog.title("Export Complete")
            dialog.geometry("500x300")
            
            ctk.CTkTextbox(dialog).pack(fill="both", expand=True, padx=20, pady=20)
            text_widget = dialog.winfo_children()[0]
            text_widget.insert("1.0", message)

class FinalCompleteApp(ctk.CTk):
    """
    FINAL COMPLETE APPLICATION
    Image → AI → 3D → Game → Playable
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize systems
        self.image_converter = ImageToGameConverter(OPENAI_API_KEY, CPP_AI_API_URL)
        self.game_builder = None  # Will be created in UI
        
        # Window setup
        self.title("Unreal AI Architect | FINAL COMPLETE EDITION")
        self.geometry("1600x1000")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.setup_ui()
    
    def setup_ui(self):
        # Left: Image Upload & Drawing
        left_panel = ctk.CTkFrame(self)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=10)
        
        self.image_canvas = ImageUploadCanvas(left_panel, self.process_image)
        self.image_canvas.pack(fill="both", expand=True)
        
        # Right: Game Builder
        right_panel = ctk.CTkFrame(self)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5,10), pady=10)
        
        self.game_builder = GameBuilderPanel(right_panel)
        self.game_builder.pack(fill="both", expand=True)
        
        # Bottom: Progress Log
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            self.log_frame,
            text="📋 Process Log",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        
        self.log_text = ctk.CTkTextbox(self.log_frame, height=150)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    def log(self, message: str):
        """Add to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
    
    def process_image(self, image_path: str, description: str):
        """Process uploaded/drawn image"""
        
        self.log(f"📸 Processing image: {image_path}")
        self.log(f"💬 Description: {description}")
        
        # Process in background
        threading.Thread(
            target=self.process_image_workflow,
            args=(image_path, description),
            daemon=True
        ).start()
    
    def process_image_workflow(self, image_path: str, description: str):
        """Complete image-to-game workflow"""
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Step 1: Analyze image
            self.after(0, lambda: self.log("🧠 AI analyzing image..."))
            
            results = loop.run_until_complete(
                self.image_converter.convert_to_game_asset(
                    image_path,
                    description,
                    auto_integrate=True
                )
            )
            
            # Log each step
            for step in results.get("steps", []):
                self.after(0, lambda s=step: self.log(s))
            
            # Step 2: Add to game environment
            if results.get("assets_created"):
                for asset in results["assets_created"]:
                    self.after(0, lambda a=asset: self.game_builder.add_generated_asset(a.get("asset_data", {})))
                    self.after(0, lambda: self.log("✅ Asset added to game environment!"))
            
            # Step 3: Show completion
            self.after(0, lambda: self.log("🎉 Complete! Your idea is now a game asset!"))
            self.after(0, lambda: self.log("💡 Use Game Builder panel to create your level!"))
            
        except Exception as e:
            self.after(0, lambda: self.log(f"❌ Error: {str(e)}"))
        finally:
            loop.close()

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("⚠️  Set OPENAI_API_KEY for full functionality")
    
    app = FinalCompleteApp()
    app.mainloop()
