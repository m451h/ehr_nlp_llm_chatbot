import sys
from src.search.search_engine import ChatbotSearchHandler  # adjust path if needed

def main():
    print("🤖 چت‌بات پزشکی آماده است! (برای خروج بنویسید: خروج یا exit)\n")
    chatbot = ChatbotSearchHandler()

    # You can change this to a specific condition ID from your data
    current_condition_id = input("🔹 لطفاً شناسه بیماری (condition_id) را وارد کنید: ").strip()
    if not current_condition_id:
        print("⚠️ هیچ شناسه‌ای وارد نشد. پایان برنامه.")
        sys.exit()

    print("\n✅ شروع گفتگو...\n")

    while True:
        user_input = input("👤 شما: ").strip()
        if user_input.lower() in ["exit", "خروج"]:
            print("👋 خداحافظ! مراقب سلامتی‌تون باشید 💙")
            break

        response = chatbot.handle_user_query(query=user_input, condition_id=current_condition_id)

        match response["response_type"]:
            case "direct_answer":
                print(f"\n💬 پاسخ: {response['answer']}")
                if response.get("follow_up"):
                    print(f"➕ پرسش پیشنهادی: {response['follow_up']}")
            case "clarification":
                print(f"\n❓ {response['message']}")
                if response.get("alternatives"):
                    print("🔹 سوالات مشابه:")
                    for alt in response["alternatives"]:
                        print(f"  - {alt}")
            case "condition_mismatch":
                print(f"\n⚠️ {response['message']}")
                print(f"👉 پیشنهاد: {response['suggestion']}")
            case "llm_fallback":
                print(f"\n🤔 {response['message']}")
                print(f"🧠 پیشنهاد: از مدل هوش مصنوعی برای پاسخ استفاده شود.")
            case "no_results":
                print(f"\n🚫 {response['message']}")
            case _:
                print("\n⚙️ پاسخ ناشناخته دریافت شد.")

        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()
