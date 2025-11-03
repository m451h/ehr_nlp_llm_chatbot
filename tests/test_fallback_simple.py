import os

from src.models.fallback import call_llm_fallback


print(
    call_llm_fallback(
        "چطور می‌توانم فشار خونم را کنترل کنم؟",
        "فشار خون بالا",
        [{"role": "user", "content": "سلام"}, {"role": "bot", "content": "سلام!"}]
    )
)

