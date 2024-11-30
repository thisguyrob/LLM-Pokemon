import pyautogui
import time
import base64
import json
import requests
from io import BytesIO
from PIL import Image

class PokemonAutomationMac:
    def __init__(self, api_key, model="openai/gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        # Mac-specific RetroArch default mappings
        self.button_mappings = {
            "a": "x",
            "b": "z",
            "start": "return",  # Changed from 'enter' to 'return' for Mac
            "select": "shift",  # Changed from 'rshift' to 'shift'
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right"
        }
        
        # Initialize pyautogui safely for Mac
        pyautogui.FAILSAFE = True  # Move mouse to upper-left to abort
        
    def get_retroarch_window(self):
        """
        Locate the RetroArch window on screen
        Returns tuple of (x, y, width, height) or None if not found
        """
        # Adding offset for menu bar and title bar (approximately 40-50 pixels)
        menu_offset = 70  # Adjust this value as needed
        window_x = 0
        window_y = menu_offset
        gb_width = 160 * 3  # GameBoy resolution x3
        gb_height = 144 * 3  # GameBoy resolution x3
        
        return (window_x, window_y, gb_width, gb_height)
    
    def capture_screen(self):
        """Capture the RetroArch window screenshot"""
        window_region = self.get_retroarch_window()
        if window_region is None:
            raise Exception("RetroArch window not found")
            
        # Add small delay to ensure screen capture is ready
        time.sleep(0.1)
        screenshot = pyautogui.screenshot(region=window_region)
        
        # Debug: Save screenshot to file
        screenshot.save("debug_screenshot.png")
        
        # Resize to original GameBoy resolution for the AI
        return screenshot.resize((160, 144), Image.Resampling.LANCZOS)
    
    def image_to_base64(self, image):
        """Convert PIL Image to base64 string"""
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
    
    def get_llm_suggestion(self, image_base64):
        """Get next button suggestion from vision model"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "pokemon-automation", 
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI playing Pokemon Yellow. You must respond with ONLY ONE of these exact words with no punctuation or additional text: up down left right a b start select"
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Based on this Pokemon Yellow screenshot, which single button should be pressed? Respond with only one word."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_base64
                            }
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"].strip().lower()
                # Only accept exact button matches
                valid_buttons = set(self.button_mappings.keys())
                if content in valid_buttons:
                    return content
                print(f"Invalid button response: {content}, defaulting to 'a'")
                return "a"  # Default to 'a' if response isn't valid
            else:
                print(f"API Error Response: {response.text}")
                return "a"  # Default to 'a' on error
                
        except Exception as e:
            print(f"Error in API call: {str(e)}")
            return "a"  # Default to 'a' on exception

    def press_button(self, button):
        """Press the suggested button in RetroArch"""
        if button in self.button_mappings:
            mapped_key = self.button_mappings[button]
            try:
                # Add small delay before keypress for Mac stability
                time.sleep(0.05)
                pyautogui.keyDown(mapped_key)
                time.sleep(0.1)  # Hold for 100ms
                pyautogui.keyUp(mapped_key)
                time.sleep(0.5)  # Wait between actions
            except pyautogui.FailSafeException:
                print("Failsafe triggered - cursor moved to upper-left corner")
                raise
            except Exception as e:
                print(f"Error pressing key {mapped_key}: {str(e)}")
    
    def run_automation(self, iterations=5):
        """Main automation loop"""
        print("Starting automation - move mouse to upper-left corner to abort")
        print("Make sure RetroArch window is focused!")
        
        # Give time to switch to RetroArch window
        time.sleep(3)
        
        for i in range(iterations):
            try:
                # 1. Capture current game state
                screenshot = self.capture_screen()
                
                # 2. Convert image to base64
                image_base64 = self.image_to_base64(screenshot)
                
                # 3. Get LLM suggestion
                suggested_button = self.get_llm_suggestion(image_base64)
                
                # 4. Press the suggested button
                self.press_button(suggested_button)
                
                # Log the action
                print(f"Iteration {i+1}: Pressed {suggested_button}")
                
                # Add 1 second delay between iterations
                time.sleep(2)
                
            except pyautogui.FailSafeException:
                print("Automation aborted by user")
                break
            except Exception as e:
                print(f"Error in iteration {i+1}: {str(e)}")
                continue

def test_screen_capture():
    automation = PokemonAutomationMac("test")
    screenshot = automation.capture_screen()
    screenshot.save("test_capture.png")
    print("Screenshot saved as test_capture.png")

if __name__ == "__main__":
    API_KEY = "add-your-own-api-key-here"
    automation = PokemonAutomationMac(API_KEY)
    automation.run_automation(iterations=100)
