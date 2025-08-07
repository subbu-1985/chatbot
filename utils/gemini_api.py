import requests
import json

class GeminiAPI:
    """Handles API communication with Google Gemini for AI text generation."""

    def __init__(self, api_key=None):
        self.api_key = api_key or "AIzaSyBljIYoGCRFHOPccj_Xpy5DaNPjvM7Qg5s"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-2.0-flash"
        self.endpoint = f"{self.base_url}/models/{self.model}:generateContent"
        self.headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }
        if not self.api_key:
            raise ValueError("Google Gemini API key is required")

    def generate_response(self, user_input, conversation_history=None):
        """Generate AI response using Gemini API."""
        contents = []
        if conversation_history:
            for msg in conversation_history:
                # Ensure each message has a valid role: 'user' or 'model'
                role = msg.get("role", "user")
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
        # Add the current user input
        contents.append({
            "role": "user",
            "parts": [{"text": user_input}]
        })
        payload = {"contents": contents}
        try:
            response = requests.post(self.endpoint, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "I'm sorry, I couldn't generate a response."
        except requests.exceptions.RequestException as e:
            print(f"Error calling Gemini API: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response content: {e.response.text}")
            return "I'm sorry, I'm having trouble connecting to the AI service."
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return "I'm sorry, I received an invalid response from the AI service."
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "I'm sorry, an unexpected error occurred."

    def generate_streaming_response(self, user_input, conversation_history=None):
        """Generate streaming AI response using Gemini API (simulated, as Gemini API does not support streaming)."""
        response = self.generate_response(user_input, conversation_history)
        yield response

    def test_connection(self):
        """Test the connection to the Gemini API."""
        try:
            # Test with a simple POST to the model endpoint
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": "Hello"}]
                    }
                ]
            }
            response = requests.post(self.endpoint, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return "Connection successful"
        except requests.exceptions.RequestException as e:
            return f"Connection failed: {e}"
