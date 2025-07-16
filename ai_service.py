from typing import List, Dict
import os

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

# Placeholder for external AI API (Gemini) integration (v0.5)
async def gemini_analyze_text(text: str) -> Dict:
    # This is a placeholder. Actual implementation would involve:
    # 1. Importing google.generativeai as genai
    # 2. Setting genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    # 3. Calling a model, e.g., model = genai.GenerativeModel('gemini-pro')
    # 4. Processing the response for sentiment and entities.
    print(f"[AI Service] Simulating Gemini analysis for: {text[:50]}...")
    return {
        "sentiment": {"label": "neutral", "score": 0.5},
        "entities": [],
        "mock_data": True # Indicate this is mock data
    }
