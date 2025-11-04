"""
Condition Educator Agent
Generates personalized educational notes for conditions based on patient clinical data
"""
import os
from typing import Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from openai import OpenAI
    _HAS_OPENAI = True
except Exception as e:
    print("⚠️ OpenAI import failed:", e)
    _HAS_OPENAI = False


def generate_condition_note(condition_name: str, clinical_data: Dict) -> Optional[str]:
    """
    Generate a personalized educational note for a condition
    
    Args:
        condition_name: Name of the condition (e.g., "دیابت نوع ۲")
        clinical_data: Dictionary with patient's clinical data
    
    Returns:
        Generated educational note in Persian, or None if error
    """
    try:
        if not _HAS_OPENAI:
            return None

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        client = OpenAI(api_key=api_key, base_url=api_base)

        # Format clinical data for the prompt
        data_summary = ""
        for key, value in clinical_data.items():
            data_summary += f"- {key}: {value}\n"

        system_prompt = (
            "You are a medical educator assistant. Generate a comprehensive, "
            "personalized educational note in Persian (fa-IR) about the given condition. "
            "Use the patient's clinical data to personalize the information. "
            "Make it detailed, educational, and easy to understand. "
            "Always include a disclaimer that this is educational information and not medical advice."
        )

        user_prompt = f"""بیماری: {condition_name}

داده‌های بالینی بیمار:
{data_summary}

لطفا یک یادداشت آموزشی جامع و شخصی‌سازی شده درباره این بیماری بنویسید که با توجه به داده‌های بالینی بیمار باشد."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
        )

        note = completion.choices[0].message.content.strip()
        return note

    except Exception as e:
        print(f"❌ Exception in generate_condition_note: {e}")
        return None

