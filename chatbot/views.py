# ai_medical_assistant/chatbot/views.py
import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from chatbot.models import ChatHistory

# --- Lazy load model only when first used ---
tokenizer = None
model = None

def load_small_model():
    """Load DialoGPT-small model only once (on demand)."""
    global tokenizer, model
    if tokenizer is not None and model is not None:
        return

    print("🔹 Loading lightweight DialoGPT-small model (lazy)...")
    tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small", cache_dir="models/")
    model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small", cache_dir="models/")
    print("✅ Chatbot model ready (DialoGPT-small).")


# --- simple rule-based health advice ---
RULES = {
    # 🌡️ Common Symptoms
    "fever": "Fever usually means your body is fighting an infection. Rest well, drink fluids, and take paracetamol if needed. If your temperature stays above 102°F or lasts more than 3 days, visit a doctor.",
    "cold": "A common cold is usually viral. Rest, stay hydrated, and inhale steam for relief. If you develop high fever or sinus pain, consult a doctor.",
    "cough": "A cough may come from infection, allergies, or acid reflux. Stay away from smoke, drink warm water with honey, and consult a doctor if it lasts more than 2 weeks.",
    "headache": "Headaches can be caused by dehydration, tension, or eye strain. Rest, drink water, and avoid screens. Severe or recurring headaches may need medical evaluation.",
    "sore throat": "It’s often caused by viral infection or dryness. Gargle with warm salt water and avoid cold drinks. If you notice white patches, see a doctor.",
    "body pain": "Mild body aches can result from infection, overexertion, or fatigue. Take rest and drink fluids. Persistent pain may require a check-up.",
    "fatigue": "Tiredness may be due to stress, poor nutrition, or thyroid issues. Sleep adequately, eat balanced meals, and get blood tests if it continues.",
    "nausea": "Can occur due to infection, motion sickness, or gastritis. Sip water or ginger tea slowly and avoid heavy food. Seek medical help if frequent.",
    "vomiting": "Commonly due to food poisoning or infection. Drink oral rehydration solutions. Persistent vomiting may require medical care.",
    "diarrhea": "Loose motions often mean infection or food intolerance. Stay hydrated, eat plain food, and see a doctor if it lasts more than 2 days.",
    "constipation": "Eat more fiber (fruits, vegetables), drink water, and exercise. If you see blood in stools, contact your doctor.",
    "dizziness": "Could be due to dehydration, low sugar, or low BP. Sit down, drink water, and rest. Recurrent dizziness should be checked by a doctor.",
    "chest pain": "Mild chest pain may be muscular, but sharp pain or pressure may indicate heart issues. Seek emergency care immediately if in doubt.",
    "back pain": "Often caused by posture, strain, or disc issues. Stretch regularly, maintain good posture, and apply warm compress.",
    "joint pain": "Can occur due to arthritis or overuse. Do light exercise, take warm baths, and consider vitamin D and calcium intake.",
    "abdominal pain": "Can result from gas, infection, or ulcers. Avoid spicy food and get checked if pain is severe or localized.",
    "shortness of breath": "May be due to asthma, anxiety, or heart problems. Sit upright and breathe slowly. If it persists, seek immediate help.",

    # 🦠 Infectious Diseases
    "flu": "Flu causes fever, sore throat, and fatigue. Rest, drink warm fluids, and take paracetamol if needed. Avoid contact with others.",
    "malaria": "Malaria causes high fever with chills and sweating. Get a blood test immediately and follow doctor-prescribed medication.",
    "dengue": "Dengue presents with fever, joint pain, and rash. Drink plenty of fluids and monitor platelets. Avoid painkillers like ibuprofen.",
    "typhoid": "Typhoid leads to high fever, weakness, and abdominal discomfort. Get a Widal test and follow antibiotics as prescribed.",
    "covid": "Common symptoms include fever, cough, and loss of smell. Isolate, monitor oxygen levels, and see a doctor if breathing becomes difficult.",
    "tuberculosis": "TB causes chronic cough, fever, and weight loss. Needs long-term antibiotics under doctor supervision.",
    "pneumonia": "Symptoms include cough, fever, and chest pain. It requires antibiotics and medical attention.",
    "bronchitis": "Persistent cough with mucus suggests bronchitis. Avoid smoking and rest. Antibiotics may be needed.",
    "sinusitis": "Facial pressure, nasal congestion, and headache indicate sinusitis. Steam inhalation and nasal sprays may help.",
    "tonsillitis": "Sore throat with swollen tonsils. Gargle salt water and see a doctor if frequent.",
    "urinary infection": "Burning urination and lower abdominal pain suggest UTI. Drink water and see a doctor for antibiotics.",
    "hepatitis": "Fatigue and yellow eyes suggest hepatitis. Avoid alcohol and fatty foods, and consult a doctor immediately.",
    "jaundice": "Yellowing of skin and eyes indicates liver issues. Get liver tests done and rest.",
    "chickenpox": "Fever with itchy rash. Rest and avoid scratching. Isolate until spots crust over.",
    "measles": "Fever with rash and red eyes. Rest, hydration, and vitamin A supplements may be advised.",
    "mumps": "Swelling near jaw and fever. Rest, drink fluids, and isolate to prevent spread.",
    "typhus": "High fever and rash. Needs antibiotics prescribed by a doctor.",

    # ❤️ Chronic & Metabolic Diseases
    "diabetes": "Monitor your blood sugar, eat low-sugar foods, and exercise daily. Take insulin or medicines as prescribed.",
    "hypertension": "High blood pressure needs lifestyle control. Reduce salt, manage stress, and take medicines regularly.",
    "cholesterol": "Avoid fried foods and exercise. Eat more fruits, oats, and green veggies.",
    "thyroid": "Can cause fatigue or weight changes. Take your medication regularly and get periodic tests.",
    "asthma": "Avoid dust and allergens. Use prescribed inhalers and avoid triggers like cold air or smoke.",
    "arthritis": "Joint stiffness and pain are common. Stay active, do light stretching, and use warm compresses.",
    "osteoporosis": "Weak bones occur from calcium or vitamin D deficiency. Eat dairy, get sunlight, and exercise.",
    "anemia": "Caused by low iron. Eat green vegetables, jaggery, and red meat if non-vegetarian.",
    "migraine": "Rest in a dark room and avoid loud noises. Maintain regular sleep and hydration.",
    "gout": "Avoid red meat and alcohol. Drink more water and take medicines to control uric acid.",
    "obesity": "Eat smaller meals and exercise regularly. Focus on balanced nutrition.",
    "ulcer": "Avoid spicy food and coffee. Eat soft, non-acidic food and take medicines as prescribed.",
    "acid reflux": "Avoid lying down after eating and skip spicy food. Antacids can help temporarily.",
    "fatty liver": "Avoid alcohol and fried foods. Exercise regularly and maintain a healthy weight.",
    "pcos": "Maintain healthy weight and diet. Consult your gynecologist for hormonal therapy if needed.",
    "piles": "Eat fiber-rich foods, drink water, and avoid straining during bowel movements.",
    "hypothyroidism": "Take your thyroid medicine daily on an empty stomach. Regular testing is important.",
    "epilepsy": "Follow medication strictly and avoid triggers like stress or sleep deprivation.",
    "stroke": "Seek emergency care for sudden weakness or slurred speech. Rehabilitation is key.",
    "heart attack": "Chest pressure with sweating and pain radiating to arm or jaw needs immediate emergency care.",

    # 🧠 Mental Health
    "depression": "Persistent sadness or loss of interest may indicate depression. Talk to a counselor or trusted person.",
    "anxiety": "Practice deep breathing, meditation, and limit caffeine. Therapy may help.",
    "stress": "Take breaks, sleep well, and talk about your feelings. Regular relaxation helps.",
    "insomnia": "Keep a consistent sleep schedule and avoid screens before bed.",
    "panic attack": "Take slow, deep breaths. Focus on calming surroundings and seek therapy if frequent.",
    "ocd": "Obsessive behaviors may need counseling or therapy. Professional help can manage symptoms.",

    # 👩‍⚕️ Women’s & Reproductive Health
    "menstrual pain": "Use a heating pad and stay hydrated. If cramps are severe, see a gynecologist.",
    "pregnancy": "Eat balanced meals, take prenatal vitamins, and get regular check-ups.",
    "menopause": "Hot flashes and mood changes are common. Maintain a healthy lifestyle and consult your doctor if symptoms are severe.",
    "breast lump": "Any lump should be examined by a doctor immediately.",
    "vaginal infection": "Itching or discharge may indicate infection. Maintain hygiene and see a gynecologist.",

    # 👶 Child & Pediatric
    "child fever": "Keep the child hydrated and check temperature regularly. See a pediatrician if it exceeds 102°F.",
    "chickenpox in child": "Isolate and give soothing baths. Avoid scratching to prevent scars.",
    "diaper rash": "Keep the area dry, use gentle creams, and change diapers often.",
    "ear pain in child": "Keep ears dry and consult a pediatrician if it persists.",

    # 🚑 Emergency & First Aid
    "bleeding": "Apply pressure to stop bleeding and keep the wound clean. Seek help if deep or continuous.",
    "burn": "Cool the area with water (not ice) and cover lightly. For large burns, seek emergency care.",
    "fracture": "Immobilize the area and visit the emergency room immediately.",
    "snake bite": "Stay calm, don’t suck the venom, and get emergency medical help.",
    "heart attack": "Call emergency services immediately. Chew aspirin if not allergic.",
    "stroke": "If sudden weakness or slurred speech occurs, reach a hospital immediately.",

    # 💬 General Health
    "nutrition": "Eat balanced meals with proteins, fiber, and vitamins. Avoid junk food.",
    "hydration": "Drink at least 2–3 liters of water daily to maintain body balance.",
    "exercise": "30 minutes of daily exercise boosts health and immunity.",
    "sleep": "Adults need 7–9 hours of sleep for recovery and mental clarity.",
    "self care": "Take breaks, eat on time, and do what relaxes you. Health includes your mind and body.",
    "default": "I'm not sure I understand. Could you describe your symptoms in more detail?",

    "hello": "Hello there! 👋 How are you feeling today?",
    "hi": "Hi! I’m your AI medical assistant. How can I help with your health?",
    "hey": "Hey! How’s your day going so far?",
    "good morning": "Good morning ☀️! Wishing you a healthy and energetic day!",
    "good evening": "Good evening 🌙! How are you feeling tonight?",
    "how are you": "I’m doing great, thanks for asking! I hope you’re feeling well too. What brings you here today?",
    "who are you": "I’m MedBot 🤖 — your AI health companion, designed to guide you with medical info and lifestyle tips!",
    "what is your name": "You can call me MedBot 🩺 — your friendly virtual health assistant!",
    "thank you": "You’re most welcome! I’m glad I could help 😊",
    "thanks": "No problem at all! Stay healthy and take care 💚",
    "bye": "Goodbye! Wishing you good health and happiness!",
    "goodbye": "Take care! Don’t forget to rest and stay hydrated 👋",
    "ok": "Got it! Is there anything else you’d like to discuss?",
    "fine": "That’s great to hear! 😊 How can I assist you further?",
    "not feeling well": "I’m sorry to hear that. Can you describe your symptoms so I can guide you?",
    "i am sick": "I hope you recover soon. Tell me what symptoms you’re experiencing so I can assist you better.",
    "bored": "Let’s cheer you up! Try a short walk, listen to music, or watch something light.",
    "sad": "I’m here for you. It’s okay to feel down sometimes. Talking or doing something creative can help.",
    "lonely": "You’re not alone — I’m right here. Try connecting with a friend or loved one.",
    "tell me a joke": "Sure 😄 — Why did the scarecrow win an award? Because he was outstanding in his field!",
    "motivation": "You’re stronger than you think 💪. Every small step towards good health counts.",
    "self care": "Self-care means resting, eating well, moving your body, and saying no when you need to. You deserve it 💖.",
}


def generate_ai_reply(user_input: str, memory=None) -> str:
    """
    Generate a context-aware short reply using DialoGPT.
    memory = list of last few messages [{message:..., response:...}]
    """
    try:
        # 🧠 Combine memory + new message into conversation context
        conversation_context = ""
        if memory:
            # Include last 3 user-bot exchanges for better context
            for chat in memory[-3:]:
                conversation_context += f"User: {chat['message']}\nBot: {chat['response']}\n"
        conversation_context += f"User: {user_input}\nBot:"

        # 🔹 Tokenize and generate
        load_small_model()  # ensure model is loaded

        input_ids = tokenizer.encode(conversation_context + tokenizer.eos_token, return_tensors="pt")

        output_ids = model.generate(
            input_ids,
            max_length=220,
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=3,
            top_k=40,
            top_p=0.9,
            temperature=0.8,
        )

        reply = tokenizer.decode(output_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)

        # 🩺 Fallback reply if model gives empty output
        if not reply.strip():
            reply = "I'm here to help! Could you tell me more about your symptoms?"

        # Add disclaimer automatically
        reply += "\n\n⚕️ *Disclaimer: I'm an AI assistant, not a doctor.*"
        return reply

    except Exception as e:
        print("❌ AI reply generation error:", e)
        return "⚠️ Sorry, I encountered an issue while processing your request."


def chatbot_home(request):
    """Render chatbot page."""
    return render(request, "chatbot/chatbot_home.html")

MAX_MEMORY = 10

from deep_translator import GoogleTranslator

def translate_text(text, src='auto', dest='en'):
    try:
        return GoogleTranslator(source=src, target=dest).translate(text)
    except Exception:
        return text
@csrf_exempt
def chatbot_reply(request):
    """Handle AJAX chat requests — English only, fully offline."""
    if request.method != "POST":
        return JsonResponse({"response": "Invalid request method."})

    user_msg = request.POST.get("message", "").strip()
    if not user_msg:
        return JsonResponse({"response": "Please type something."})

    # ✅ Session-based memory
    memory = request.session.get("chat_memory", [])

    # 🧠 Rule-based quick replies first
    bot_reply = None
    for keyword, response in RULES.items():
        if keyword.lower() in user_msg.lower():
            bot_reply = response
            break

    # 💬 If not found in RULES, use the AI model
    if not bot_reply:
        try:
            bot_reply = generate_ai_reply(user_msg, memory)
        except Exception as e:
            print("❌ AI reply error:", e)
            bot_reply = "⚠️ Sorry, I encountered an issue generating a response."

    # 💾 Save to DB (if logged in)
    try:
        user = request.user if request.user.is_authenticated else None
        ChatHistory.objects.create(user=user, message=user_msg, response=bot_reply)
    except Exception as e:
        print("⚠️ Chat save error:", e)

    # 🧠 Update short-term memory
    memory.append({"message": user_msg, "response": bot_reply})
    if len(memory) > MAX_MEMORY:
        memory = memory[-MAX_MEMORY:]
    request.session["chat_memory"] = memory

    # ✅ Return response
    return JsonResponse({"response": bot_reply})


@csrf_exempt
def delete_chat_history(request):
    """Delete specific or all chat messages for the logged-in user."""
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Login required."})

    if request.method == "POST":
        chat_id = request.POST.get("chat_id")
        user = request.user

        if chat_id == "all":
            ChatHistory.objects.filter(user=user).delete()
            request.session["chat_memory"] = []
            return JsonResponse({"status": "success", "message": "All chat history deleted."})

        elif chat_id and chat_id.isdigit():
            ChatHistory.objects.filter(user=user, id=chat_id).delete()
            return JsonResponse({"status": "success", "message": "Message deleted."})

    return JsonResponse({"status": "error", "message": "Invalid request."})

@login_required
def view_chat_history(request):
    """Display user's saved chat history."""
    user = request.user
    history = ChatHistory.objects.filter(user=user).order_by('-timestamp')
    return render(request, "chatbot/chat_history.html", {"history": history})

