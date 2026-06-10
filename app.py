import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# Load configurations from .env file
load_dotenv(override=True)

# Page Configuration
st.set_page_config(
    page_title="Globeam AI Assistant",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    /* Theme configuration overrides */
    .stApp {
        background-color: #0f1115;
        color: #e2e8f0;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    
    /* Title and Header style */
    .brand-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffcc00 0%, #ff6600 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        text-shadow: 0px 4px 20px rgba(255, 204, 0, 0.15);
    }
    
    .brand-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
    }
    
    /* Sidebar Custom styling */
    section[data-testid="stSidebar"] {
        background-color: #161920 !important;
        border-right: 1px solid #272c38;
    }
    
    /* Chat bubbles styling */
    .stChatMessage {
        background-color: #161920 !important;
        border: 1px solid #272c38;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Quick option buttons */
    .stButton>button {
        background: linear-gradient(135deg, #272c38 0%, #1e222b 100%) !important;
        color: #e2e8f0 !important;
        border: 1px solid #3b4252 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        border-color: #ffcc00 !important;
        color: #ffcc00 !important;
        box-shadow: 0px 0px 12px rgba(255, 204, 0, 0.2);
    }
    
    /* Alert style overrides */
    .stAlert {
        background-color: #1e222b !important;
        border: 1px solid #272c38 !important;
    }
</style>
""", unsafe_allow_html=True)

# Load database file
DATABASE_FILE = "globeam_products.txt"
db_content = ""
if os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, "r", encoding="utf-8") as f:
        db_content = f.read()
else:
    st.error(f"Database file '{DATABASE_FILE}' not found. Please extract the data first.")

# System prompts setup (Bilingual)
SYSTEM_INSTRUCTION_EN = f"""
You are Globeam AI Assistant, an expert AI representative of Globeam Radiant Pvt. Ltd.

Your purpose is to help customers, dealers, distributors, sales representatives, and website visitors by answering questions based ONLY on the Globeam product catalog and company information provided in the database below.

===========================================================
STRICT RESPONSE RULES
===========================================================
1. Answer ONLY using information available in the provided database content.
2. Never invent specifications, battery capacities, warranties, charging times, backup times, beam ranges, or features.
3. If information is not available, respond exactly:
"Sorry, this information is not available in the current Globeam database."
4. Do not guess.
5. Do not generate fake product details.
6. Do not provide competitor recommendations.
7. Always remain professional and helpful.

===========================================================
PRODUCT RECOMMENDATION RULES
===========================================================
When a user asks for a recommendation (e.g. "I need a torch for farming", "I need a long backup torch", "I need a study lamp", etc.):
Recommend the most suitable Globeam product from the database and explain WHY.
Format the recommendation clearly like this:

Recommended Product: [Product Name]

Reason:
- [Point 1]
- [Point 2]
- [Point 3]

===========================================================
COMPARISON MODE
===========================================================
When a user asks: "Compare Product A and Product B"
Provide a comparison strictly in this markdown table format:

Product Comparison

Feature | Product A | Product B
Battery | ... | ...
Backup | ... | ...
Charging | ... | ...
Special Features | ... | ...

Then provide a short recommendation.

===========================================================
TROUBLESHOOTING MODE
===========================================================
When users ask troubleshooting questions (e.g. "My torch is not charging", "My fan is not working", etc.):
First provide simple troubleshooting steps using available product information.
If information is unavailable or does not solve the issue, respond:
"Please contact Globeam customer support for further assistance."

===========================================================
CUSTOMER / DEALER / DISTRIBUTOR SUPPORT MODE
===========================================================
- Answer clearly and concisely.
- Never provide inventory levels or pricing unless explicitly present in the database.
- Be concise, use bullet points when appropriate, and mention exact product names, exact battery capacities, and backup times when available.
- Do not write long paragraphs unless requested.

===========================================================
OUT OF SCOPE QUESTIONS
===========================================================
If asked unrelated questions (politics, coding, sports, movies, general knowledge, etc.), respond exactly:
"I am Globeam AI Assistant and can only help with Globeam products and company-related information."

===========================================================
GLOBEAM PRODUCT DATABASE
===========================================================
{db_content}
"""

SYSTEM_INSTRUCTION_HI = f"""
आप Globeam AI Assistant हैं, जो Globeam Radiant Pvt. Ltd. के एक विशेषज्ञ AI प्रतिनिधि हैं।

आपका उद्देश्य नीचे दिए गए डेटाबेस में दी गई केवल Globeam उत्पाद सूची और कंपनी की जानकारी के आधार पर प्रश्नों का उत्तर देकर ग्राहकों, डीलरों, वितरकों, बिक्री प्रतिनिधियों और वेबसाइट आगंतुकों की सहायता करना है।

आपको केवल हिंदी भाषा (Hindi Language) में उत्तर देना है।

===========================================================
सख्त प्रतिक्रिया नियम (STRICT RESPONSE RULES)
===========================================================
1. केवल प्रदान की गई डेटाबेस सामग्री में उपलब्ध जानकारी का उपयोग करके उत्तर दें।
2. कभी भी विशिष्टताओं (specifications), बैटरी क्षमता, वारंटी, चार्जिंग समय, बैकअप समय, बीम रेंज या सुविधाओं का मनगढ़ंत आविष्कार न करें।
3. यदि जानकारी उपलब्ध नहीं है, तो बिल्कुल यही उत्तर दें:
"क्षमा करें, यह जानकारी वर्तमान Globeam डेटाबेस में उपलब्ध नहीं है।"
4. अनुमान न लगाएं।
5. नकली उत्पाद विवरण उत्पन्न न करें।
6. प्रतिस्पर्धी ब्रांडों की सिफारिशें न करें।
7. हमेशा पेशेवर और मददगार बने रहें।

===========================================================
उत्पाद अनुशंसा नियम (PRODUCT RECOMMENDATION RULES)
===========================================================
जब कोई उपयोगकर्ता सिफारिश के लिए पूछे (जैसे "मुझे खेती के लिए टॉर्च चाहिए", "मुझे लंबे बैकअप वाली टॉर्च चाहिए", "मुझे स्टडी लैंप चाहिए", आदि):
डेटाबेस से सबसे उपयुक्त Globeam उत्पाद की सिफारिश करें और स्पष्ट करें कि क्यों (WHY)।
सिफारिश को इस तरह स्पष्ट रूप से प्रारूपित (format) करें:

अनुशंसित उत्पाद (Recommended Product): [उत्पाद का नाम]

कारण (Reason):
- [बिंदु 1]
- [बिंदु 2]
- [बिंदु 3]

===========================================================
तुलना मोड (COMPARISON MODE)
===========================================================
जब कोई उपयोगकर्ता पूछे: "Product A और Product B की तुलना करें"
इस मार्कडाउन तालिका प्रारूप में सख्ती से तुलना प्रदान करें:

उत्पाद तुलना (Product Comparison)

विशेषता (Feature) | उत्पाद A (Product A) | उत्पाद B (Product B)
बैटरी (Battery) | ... | ...
बैकअप (Backup) | ... | ...
चार्जिंग (Charging) | ... | ...
विशेष सुविधाएं (Special Features) | ... | ...

फिर एक संक्षिप्त अनुशंसा प्रदान करें।

===========================================================
समस्या निवारण मोड (TROUBLESHOOTING MODE)
===========================================================
जब उपयोगकर्ता समस्या निवारण प्रश्न पूछते हैं (जैसे "मेरी टॉर्च चार्ज नहीं हो रही है", "मेरा पंखा काम नहीं कर रहा है", आदि):
सबसे पहले उपलब्ध उत्पाद जानकारी का उपयोग करके सरल समस्या निवारण कदम प्रदान करें।
यदि जानकारी अनुपलब्ध है या समस्या का समाधान नहीं करती है, तो उत्तर दें:
"कृपया आगे की सहायता के लिए Globeam ग्राहक सहायता से संपर्क करें।"

===========================================================
ग्राहक / डीलर / वितरक सहायता मोड (SUPPORT MODE)
===========================================================
- स्पष्ट और संक्षेप में उत्तर दें।
- जब तक डेटाबेस में स्पष्ट रूप से मौजूद न हो, तब तक इन्वेंट्री स्तर या मूल्य निर्धारण प्रदान न करें।
- संक्षिप्त रहें, उपयुक्त होने पर बुलेट पॉइंट्स का उपयोग करें, और उपलब्ध होने पर सटीक उत्पाद नाम, सटीक बैटरी क्षमता और बैकअप समय का उल्लेख करें।
- जब तक अनुरोध न किया जाए, लंबे पैराग्राफ न लिखें।

===========================================================
दायरे से बाहर के प्रश्न (OUT OF SCOPE QUESTIONS)
===========================================================
यदि असंबंधित प्रश्न (राजनीति, कोडिंग, खेल, फिल्में, सामान्य ज्ञान, आदि) पूछे जाएं, तो बिल्कुल यही उत्तर दें:
"मैं Globeam AI Assistant हूँ और मैं केवल Globeam उत्पादों और कंपनी से संबंधित जानकारी में ही सहायता कर सकता हूँ।"

===========================================================
ग्लोबीम उत्पाद डेटाबेस (GLOBEAM PRODUCT DATABASE)
===========================================================
{db_content}
"""

UI_TEXT = {
    "English": {
        "brand_title": "GLOBEAM AI ASSISTANT",
        "brand_subtitle": "Your expert assistant for Globeam Rechargeable Torches, Solar Lights, Study Lamps, Fans, and Appliances.",
        "status_title": "System Status",
        "active": "🟢 Active (Pool: {count} Backend Key{s})",
        "error": "🔴 Connection Error: API Keys missing in backend (.env)",
        "info": "Please set the `GEMINI_API_KEYS` in your local `.env` file.",
        "select_model": "Select Model",
        "select_language": "Language / भाषा",
        "quick_links": "Quick Links / Support",
        "made_by": "Made with ❤️ for Globeam Radiant Pvt. Ltd.",
        "quick_farmer": "🚜 Farmer Torch Recommendation",
        "quick_compare": "⚖️ Compare Sainik & Sultan",
        "quick_lamp": "💡 Study Lamp Search",
        "quick_fan": "🔧 Fan Troubleshooting",
        "farmer_query": "I need a torch for farming/agriculture use.",
        "compare_query": "Compare Sainik and Sultan",
        "lamp_query": "I need a rechargeable study lamp.",
        "fan_query": "My rechargeable fan is not working.",
        "chat_input_placeholder": "Ask about Globeam products...",
        "analyzing": "Analyzing Globeam Database...",
        "audio_input_label": "🎤 Or Record Voice Command (English/Hindi)",
        "transcribing": "Transcribing voice command...",
        "transcription_success": "Transcribed: \"{text}\""
    },
    "Hindi (हिंदी)": {
        "brand_title": "ग्लोबीम एआई सहायक",
        "brand_subtitle": "ग्लोबीम रिचार्जेबल टॉर्च, सोलर लाइट, स्टडी लैंप, पंखे और उपकरणों के लिए आपका विशेषज्ञ सहायक।",
        "status_title": "सिस्टम की स्थिति",
        "active": "🟢 सक्रिय (पूल: {count} बैकएंड कुंजी)",
        "error": "🔴 कनेक्शन त्रुटि: बैकएंड में एपीआई कुंजियाँ गायब हैं (.env)",
        "info": "कृपया अपनी स्थानीय `.env` फ़ाइल में `GEMINI_API_KEYS` सेट करें।",
        "select_model": "मॉडल चुनें",
        "select_language": "Language / भाषा",
        "quick_links": "त्वरित संपर्क / सहायता",
        "made_by": "Globeam Radiant Pvt. Ltd. के लिए ❤️ के साथ बनाया गया।",
        "quick_farmer": "🚜 किसान टॉर्च सिफारिश",
        "quick_compare": "⚖️ सैनिक और सुल्तान की तुलना",
        "quick_lamp": "💡 स्टडी लैंप खोजें",
        "quick_fan": "🔧 पंखे का समस्या निवारण",
        "farmer_query": "मुझे खेती/कृषि उपयोग के लिए टॉर्च की आवश्यकता है।",
        "compare_query": "सैनिक और सुल्तान की तुलना करें",
        "lamp_query": "मुझे एक रिचार्जेबल स्टडी लैंप की आवश्यकता है।",
        "fan_query": "मेरा रिचार्जेबल पंखा काम नहीं कर रहा है।",
        "chat_input_placeholder": "Globeam उत्पादों के बारे में पूछें...",
        "analyzing": "Globeam डेटाबेस का विश्लेषण किया जा रहा है...",
        "audio_input_label": "🎤 या आवाज से निर्देश दें (अंग्रेजी/हिंदी)",
        "transcribing": "आवाज को पाठ में बदला जा रहा है...",
        "transcription_success": "ट्रांसक्राइब किया गया: \"{text}\""
    }
}

# API Key Pool configuration
api_keys_raw = os.environ.get("GEMINI_API_KEYS", "")
api_keys = []

if api_keys_raw:
    # Split by comma and clean up whitespace and quotes
    api_keys = [k.strip().strip('"').strip("'") for k in api_keys_raw.split(",") if k.strip()]
else:
    # Fallback to single key env variable
    single_key = os.environ.get("GEMINI_API_KEY", "")
    if single_key:
        api_keys = [single_key.strip().strip('"').strip("'")]

# Filter out placeholder template keys
api_keys = [k for k in api_keys if k not in ["your_first_key_here", "your_second_key_here", "your_third_key_here"]]

# Function to query Gemini with automatic rotation on failure
def call_gemini_with_rotation(prompt, model_name, language):
    if not api_keys:
        return "ERROR: Backend API configuration is missing. Please add a valid key to the `.env` file."
    
    # Store active key index in session state to avoid resetting on every run
    if "api_key_index" not in st.session_state:
        st.session_state.api_key_index = 0
        
    num_keys = len(api_keys)
    attempts = 0
    
    system_instruction = SYSTEM_INSTRUCTION_HI if language == "Hindi (हिंदी)" else SYSTEM_INSTRUCTION_EN
    
    while attempts < num_keys:
        current_idx = (st.session_state.api_key_index + attempts) % num_keys
        key = api_keys[current_idx]
        
        try:
            # Configure with the current key
            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            
            # Update the starting index to the successful key for future requests
            st.session_state.api_key_index = current_idx
            return response.text
            
        except Exception as e:
            error_str = str(e)
            # Log the error to stdout/terminal for system inspection
            print(f"[API Key Warning] Key index {current_idx} failed: {error_str}")
            
            # Check if it's a quota / limit / auth error
            # If so, we rotate to the next key
            attempts += 1
            
    # If we exited the loop, all keys failed
    print("[API Key Error] All keys in the pool have failed or exhausted.")
    return "Sorry, all backend connection channels are currently busy. Please try again in a few minutes."


# Function to transcribe audio using Gemini with key rotation
def transcribe_audio(audio_bytes, mime_type):
    if not api_keys:
        return None
        
    if "api_key_index" not in st.session_state:
        st.session_state.api_key_index = 0
        
    num_keys = len(api_keys)
    attempts = 0
    
    while attempts < num_keys:
        current_idx = (st.session_state.api_key_index + attempts) % num_keys
        key = api_keys[current_idx]
        
        try:
            genai.configure(api_key=key)
            # Use gemini-2.5-flash for speech transcription
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content([
                {"mime_type": mime_type, "data": audio_bytes},
                "Please transcribe this audio file. The audio can be spoken in Hindi, English, or Hinglish. Output ONLY the plain transcription text in the language spoken (e.g. use Devanagari script for Hindi, English script for English), with no additional commentary, notes, or wrapper."
            ])
            return response.text.strip()
            
        except Exception as e:
            print(f"[Transcription Key Warning] Key index {current_idx} failed: {e}")
            attempts += 1
            
    return None


# Sidebar content
with st.sidebar:
    st.markdown('<div style="text-align: center;"><h2 style="color: #ffcc00; margin-bottom: 5px;">Globeam Radiant</h2><p style="font-size:0.85rem; color:#94a3b8;">Premium Portable Lighting & Home Solutions</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    language = st.selectbox(
        "Language / भाषा",
        options=["English", "Hindi (हिंदी)"],
        index=0
    )
    ui = UI_TEXT[language]
    
    st.subheader(ui["status_title"])
    
    if len(api_keys) > 0:
        st.success(ui["active"].format(count=len(api_keys), s='s' if len(api_keys) > 1 else ''))
    else:
        st.error(ui["error"])
        st.info(ui["info"])
        
    model_choice = st.selectbox(
        ui["select_model"],
        options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
        index=0
    )
    
    st.markdown("---")
    st.markdown(f"""
    ### {ui["quick_links"]}
    - 📧 **Email**: Care@globeamindia.com
    - 🌐 **Web**: [www.globeamindia.com](http://www.globeamindia.com)
    """)
    st.markdown(f"<p style='font-size:0.75rem; color:#64748b; margin-top:20px;'>{ui['made_by']}</p>", unsafe_allow_html=True)

# Main layout headers
st.markdown(f'<h1 class="brand-title">{ui["brand_title"]}</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="brand-subtitle">{ui["brand_subtitle"]}</p>', unsafe_allow_html=True)

# Initialize Session State for Chat History
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Quick options container
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button(ui["quick_farmer"]):
        st.session_state.chat_history.append({"role": "user", "content": ui["farmer_query"]})
with col2:
    if st.button(ui["quick_compare"]):
        st.session_state.chat_history.append({"role": "user", "content": ui["compare_query"]})
with col3:
    if st.button(ui["quick_lamp"]):
        st.session_state.chat_history.append({"role": "user", "content": ui["lamp_query"]})
with col4:
    if st.button(ui["quick_fan"]):
        st.session_state.chat_history.append({"role": "user", "content": ui["fan_query"]})

# Render previous chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Voice Input Widget
audio_file = st.audio_input(ui["audio_input_label"])
if audio_file:
    audio_bytes = audio_file.read()
    audio_hash = hash(audio_bytes)
    if st.session_state.get("last_audio_hash") != audio_hash:
        st.session_state.last_audio_hash = audio_hash
        with st.spinner(ui["transcribing"]):
            transcribed_text = transcribe_audio(audio_bytes, audio_file.type)
        if transcribed_text:
            st.session_state.chat_history.append({"role": "user", "content": transcribed_text})
            st.rerun()

# User Input and response logic
user_query = st.chat_input(ui["chat_input_placeholder"])

if user_query:
    # Append user input
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

# Check and call model if new user input was added
if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
    current_query = st.session_state.chat_history[-1]["content"]
    
    with st.chat_message("assistant"):
        with st.spinner(ui["analyzing"]):
            reply_text = call_gemini_with_rotation(current_query, model_choice, language)
            
        st.markdown(reply_text)
        st.session_state.chat_history.append({"role": "assistant", "content": reply_text})
