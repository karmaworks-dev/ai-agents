import os
from dotenv import load_dotenv

load_dotenv()

KEY = os.getenv("GEMINI_KEY")
MODEL = "gemini-1.5-flash"  # Change to 'gemini-3-pro' to test latest flagship model

if not KEY:
    print("❌ No GEMINI_KEY found in .env")
else:
    print(f"💎 Testing Model: {MODEL}...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=KEY)
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content("In one short sentence, is this a good time to buy Bitcoin?")
        # Safe accessor for text
        text = getattr(response, 'text', None) or (response.candidates[0].content.parts[0] if getattr(response, 'candidates', None) else None)
        print(f"\n✅ SUCCESS! Agent says:\n'{text}'")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print("Tip: If 'gemini-3-pro' failed, try changing MODEL to 'gemini-1.5-flash'")
