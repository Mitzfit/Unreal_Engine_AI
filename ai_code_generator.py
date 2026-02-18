"""
AI Code Generator - Integrates with Claude/OpenAI for code generation
"""

import os
from typing import Dict, Any, Optional


class AICodeGenerator:
    """Generate code using AI"""
    
    def __init__(self, api_key: str = ""):
        """Initialize code generator"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.client = None
        
        # Try to initialize with available APIs
        self._init_client()
    
    def _init_client(self):
        """Initialize AI client"""
        try:
            # Try OpenAI first
            if self.api_key:
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=self.api_key)
                    print("✓ OpenAI client initialized")
                    return
                except ImportError:
                    print("OpenAI not installed")
            
            # Fallback to mock responses
            print("⚠️  Using mock AI responses (install openai for real responses)")
            self.client = None
        
        except Exception as e:
            print(f"Error initializing AI client: {e}")
            self.client = None
    
    def generate_code(self, prompt: str, language: str = "python") -> str:
        """Generate code from prompt"""
        
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are a helpful game development AI assistant. Generate {language} code. Always format code in markdown code blocks."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )
                
                return response.choices[0].message.content
            
            except Exception as e:
                print(f"Error calling OpenAI: {e}")
                return self._get_mock_response(prompt, language)
        
        else:
            return self._get_mock_response(prompt, language)
    
    def _get_mock_response(self, prompt: str, language: str = "python") -> str:
        """Get mock AI response for testing"""
        
        prompt_lower = prompt.lower()
        
        # Cowboy character code
        if "cowboy" in prompt_lower:
            if "c++" in prompt_lower or "cpp" in prompt_lower:
                return """Here's a C++ cowboy character class:

```cpp
#include <string>
#include <iostream>

class CowboyCharacter {
private:
    std::string name;
    int health;
    int ammo;
    float speed;

public:
    CowboyCharacter(const std::string& charName, int initialHealth = 100)
        : name(charName), health(initialHealth), ammo(50), speed(1.5f) {}
    
    void drawWeapon() {
        std::cout << name << " draws their weapon!" << std::endl;
    }
    
    void shoot() {
        if (ammo > 0) {
            ammo--;
            std::cout << name << " shoots! Ammo left: " << ammo << std::endl;
        }
    }
    
    void takeDamage(int damage) {
        health -= damage;
        std::cout << name << " takes " << damage << " damage! Health: " << health << std::endl;
    }
    
    int getHealth() const { return health; }
    int getAmmo() const { return ammo; }
};
```

This creates a basic cowboy character with health, ammo, and weapon mechanics!"""
            else:
                return """Here's a Python cowboy character class:

```python
class CowboyCharacter:
    def __init__(self, name, health=100):
        self.name = name
        self.health = health
        self.ammo = 50
        self.speed = 1.5
    
    def draw_weapon(self):
        print(f"{self.name} draws their weapon!")
    
    def shoot(self):
        if self.ammo > 0:
            self.ammo -= 1
            print(f"{self.name} shoots! Ammo left: {self.ammo}")
    
    def take_damage(self, damage):
        self.health -= damage
        print(f"{self.name} takes {damage} damage! Health: {self.health}")
    
    def get_status(self):
        return f"{self.name} - Health: {self.health}, Ammo: {self.ammo}"

# Usage
player = CowboyCharacter("Lucky Luke")
player.draw_weapon()
player.shoot()
print(player.get_status())
```

This creates a simple cowboy character with basic mechanics!"""
        
        # Game mechanics
        elif "game" in prompt_lower or "mechanic" in prompt_lower:
            return """Here's a basic game loop structure:

```python
class GameLoop:
    def __init__(self):
        self.running = True
        self.entities = []
    
    def update(self, delta_time):
        \"\"\"Update game state\"\"\"
        for entity in self.entities:
            entity.update(delta_time)
    
    def render(self):
        \"\"\"Render frame\"\"\"
        for entity in self.entities:
            entity.draw()
    
    def run(self):
        \"\"\"Main game loop\"\"\"
        while self.running:
            delta_time = 16.67  # ~60 FPS
            self.update(delta_time)
            self.render()

# Create game instance
game = GameLoop()
game.run()
```

This is a basic game loop pattern used in game engines!"""
        
        # AI responses
        elif "ai" in prompt_lower or "neural" in prompt_lower:
            return """Here's a simple AI behavior system:

```python
class AIBehavior:
    def __init__(self, name):
        self.name = name
        self.state = "idle"
    
    def think(self, player_pos, self_pos):
        distance = self._distance(player_pos, self_pos)
        
        if distance < 5:
            self.state = "attack"
        elif distance < 20:
            self.state = "chase"
        else:
            self.state = "idle"
    
    def act(self):
        if self.state == "attack":
            print(f"{self.name} is attacking!")
        elif self.state == "chase":
            print(f"{self.name} is chasing!")
        else:
            print(f"{self.name} is idle")
    
    def _distance(self, pos1, pos2):
        return ((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)**0.5
```

This creates basic AI behavior states!"""
        
        # Default response
        else:
            return f"""I'd be happy to help with that!

Here's a template to get you started:

```python
# Your {language} code here
def my_function():
    \"\"\"Function description\"\"\"
    pass

if __name__ == "__main__":
    my_function()
```

Feel free to ask me:
- Generate specific code for your game
- Explain game development concepts
- Help with Unreal Engine integration
- Create character classes, game loops, AI behavior, etc.

What would you like me to help you code?"""
    
    def chat(self, message: str) -> str:
        """Generic chat response"""
        
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful Unreal Engine and game development AI assistant."
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                return response.choices[0].message.content
            
            except Exception as e:
                print(f"Error: {e}")
                return self._get_mock_chat_response(message)
        
        else:
            return self._get_mock_chat_response(message)
    
    def _get_mock_chat_response(self, message: str) -> str:
        """Get mock chat response"""
        
        msg_lower = message.lower()
        
        if "project" in msg_lower:
            return "📁 Projects help you organize your game development work. Use 'Create Project' to start a new project!"
        elif "code" in msg_lower or "generate" in msg_lower:
            return "💻 I can generate code for characters, game mechanics, AI behavior, and more. Just ask what you need!"
        elif "help" in msg_lower:
            return "🆘 I'm here to help with:\n• Code generation\n• Game design ideas\n• Unreal Engine integration\n• Character creation\n\nWhat would you like help with?"
        else:
            return "I'm ready to assist! You can ask me to generate code, explain concepts, or help with your game project."