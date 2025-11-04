import os
from typing import List, Dict, Optional

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


def call_llm_fallback(user_query: str, condition_name: str, chat_history: List[Dict], clinical_data: Optional[Dict] = None) -> Optional[str]:
    """Get an answer from an LLM when retrieval confidence is low."""
    try:
        if not _HAS_OPENAI:

            return None

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:

            return None

        api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")


        client = OpenAI(api_key=api_key, base_url=api_base)

        # Build message list
        recent_messages = []
        for m in chat_history[-6:]:
            role = m.get("role", "user")
            if role not in ("user", "bot"):
                continue
            recent_messages.append({
                "role": "user" if role == "user" else "assistant",
                "content": m.get("content", ""),
            })

        system_prompt = (
            "You are a cautious medical information assistant. "
            "Answer briefly and clearly in Persian (fa-IR). "
            "Include general educational information only. "
            "Always add a short disclaimer that this is not medical advice."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if condition_name:
            messages.append({"role": "system", "content": f"موضوع گفتگو: {condition_name}"})
        
        # Add clinical data if available
        if clinical_data:
            clinical_info = "اطلاعات بالینی بیمار:\n"
            for key, value in clinical_data.items():
                clinical_info += f"- {key}: {value}\n"
            messages.append({"role": "system", "content": clinical_info})
        
        messages += recent_messages
        messages.append({"role": "user", "content": user_query})


        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
            max_tokens=400,
        )

        text = completion.choices[0].message.content.strip()

        return text

    except Exception as e:
        print(" Exception in call_llm_fallback:", e)
        return None
