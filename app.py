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

# System prompt setup
SYSTEM_INSTRUCTION = f"""
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
def call_gemini_with_rotation(prompt, model_name):
    if not api_keys:
        return "ERROR: Backend API configuration is missing. Please add a valid key to the `.env` file."
    
    # Store active key index in session state to avoid resetting on every run
    if "api_key_index" not in st.session_state:
        st.session_state.api_key_index = 0
        
    num_keys = len(api_keys)
    attempts = 0
    
    while attempts < num_keys:
        current_idx = (st.session_state.api_key_index + attempts) % num_keys
        key = api_keys[current_idx]
        
        try:
            # Configure with the current key
            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_INSTRUCTION
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


# Sidebar content
with st.sidebar:
    st.markdown('<div style="text-align: center;"><h2 style="color: #ffcc00; margin-bottom: 5px;">Globeam Radiant</h2><p style="font-size:0.85rem; color:#94a3b8;">Premium Portable Lighting & Home Solutions</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("System Status")
    
    if len(api_keys) > 0:
        st.success(f"🟢 Active (Pool: {len(api_keys)} Backend Key{'s' if len(api_keys) > 1 else ''})")
    else:
        st.error("🔴 Connection Error: API Keys missing in backend (.env)")
        st.info("Please set the `GEMINI_API_KEYS` in your local `.env` file.")
        
    model_choice = st.selectbox(
        "Select Model",
        options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("""
    ### Quick Links / Support
    - 📧 **Email**: Care@globeamindia.com
    - 🌐 **Web**: [www.globeamindia.com](http://www.globeamindia.com)
    """)
    st.markdown("<p style='font-size:0.75rem; color:#64748b; margin-top:20px;'>Made with ❤️ for Globeam Radiant Pvt. Ltd.</p>", unsafe_allow_html=True)

# Main layout headers
st.markdown('<h1 class="brand-title">GLOBEAM AI ASSISTANT</h1>', unsafe_allow_html=True)
st.markdown('<p class="brand-subtitle">Your expert assistant for Globeam Rechargeable Torches, Solar Lights, Study Lamps, Fans, and Appliances.</p>', unsafe_allow_html=True)

# Initialize Session State for Chat History
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Quick options container
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🚜 Farmer Torch Recommendation"):
        st.session_state.chat_history.append({"role": "user", "content": "I need a torch for farming/agriculture use."})
with col2:
    if st.button("⚖️ Compare Sainik & Sultan"):
        st.session_state.chat_history.append({"role": "user", "content": "Compare Sainik and Sultan"})
with col3:
    if st.button("💡 Study Lamp Search"):
        st.session_state.chat_history.append({"role": "user", "content": "I need a rechargeable study lamp."})
with col4:
    if st.button("🔧 Fan Troubleshooting"):
        st.session_state.chat_history.append({"role": "user", "content": "My rechargeable fan is not working."})

# Render previous chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input and response logic
user_query = st.chat_input("Ask about Globeam products...")

if user_query:
    # Append user input
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

# Check and call model if new user input was added
if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
    current_query = st.session_state.chat_history[-1]["content"]
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing Globeam Database..."):
            reply_text = call_gemini_with_rotation(current_query, model_choice)
            
        st.markdown(reply_text)
        st.session_state.chat_history.append({"role": "assistant", "content": reply_text})
