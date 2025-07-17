import os
from typing import List, Dict
import google.generativeai as genai

# Configure the Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Placeholder for rule-based tagging (v0.1)
def rule_based_tagging(text: str) -> List[str]:
    tags = []
    # Example rules: simple keyword matching
    if "운동" in text:
        tags.append("운동")
    if "공부" in text:
        tags.append("공부")
    if "회의" in text:
        tags.append("회의")
    if "행복" in text or "기쁨" in text:
        tags.append("행복")
    if "슬픔" in text or "우울" in text:
        tags.append("슬픔")
    return list(set(tags)) # Return unique tags

# Gemini API integration (v0.5)
async def gemini_analyze_text(text: str) -> Dict:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key":
        print("[AI Service] Gemini API key not configured. Returning mock data.")
        return {
            "sentiment": {"label": "neutral", "score": 0.5},
            "entities": [],
            "mock_data": True
        }

    try:
        model = genai.GenerativeModel('gemini-pro')
        # Simplified prompt for demonstration
        prompt = f"""
        Analyze the following diary entry. Extract the main sentiment (positive, negative, neutral) 
        and up to 5 key entities (people, places, activities). 
        Return the result in JSON format with keys 'sentiment' and 'entities'.
        Each entity should have 'text' and 'type'.

        Entry: "{text}"
        """
        response = await model.generate_content_async(prompt)
        
        # Basic parsing, assuming the model returns a JSON string
        # In a real scenario, you'd want more robust parsing and error handling
        import json
        result = json.loads(response.text)
        result["mock_data"] = False
        return result

    except Exception as e:
        print(f"[AI Service] Error during Gemini API call: {e}")
        return {
            "sentiment": {"label": "error", "score": 0.0},
            "entities": [],
            "mock_data": True
        }
