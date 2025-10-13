import streamlit as st
import os
import time
import base64
import requests
from datetime import datetime
from spitch import Spitch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Hausa TTS Comparison",
    page_icon="🎙️",
    layout="wide"
)

# Initialize session state for history
if 'audio_history' not in st.session_state:
    st.session_state.audio_history = []

if 'current_spitch_audio' not in st.session_state:
    st.session_state.current_spitch_audio = None

if 'current_awarri_audio' not in st.session_state:
    st.session_state.current_awarri_audio = None

@st.cache_resource
def initialize_spitch():
    """Initialize Spitch client"""
    try:
        os.environ["SPITCH_API_KEY"] = os.getenv("SPITCH_API_KEY")
        return Spitch()
    except Exception as e:
        st.error(f"Failed to initialize Spitch: {str(e)}")
        return None

def generate_spitch_audio(text, voice):
    """Generate audio using Spitch TTS and return base64"""
    client = initialize_spitch()
    if not client:
        return None, 0.0
    
    try:
        start_time = time.time()
        response = client.speech.generate(
            text=text,
            language="ha",
            voice=voice.lower()
        )
        
        audio_bytes = response.read()
        latency = time.time() - start_time
        
        # Convert to base64 for storage
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return audio_base64, latency
        
    except Exception as e:
        st.error(f"Spitch generation failed: {str(e)}")
        return None, 0.0

def generate_awarri_audio(text):
    """Generate audio using Awarri TTS and return base64"""
    try:
        url = os.getenv("AWARRI_TTS_URL")
        api_key = os.getenv("AWARRI_API_KEY")
        
        if not url or not api_key:
            st.error("Awarri API credentials not configured")
            return None, 0.0
        
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        data = {
            'api_key': api_key,
            'audio_txt': text,
            'lang': 'hausa'
        }
        
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data)
        latency = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if 'base64_data' in result:
                # Already in base64 format
                return result['base64_data'], latency
            else:
                st.error("No 'base64_data' in Awarri response")
                return None, 0.0
        else:
            st.error(f"Awarri API error: {response.status_code} - {response.text}")
            return None, 0.0
            
    except Exception as e:
        st.error(f"Awarri generation failed: {str(e)}")
        return None, 0.0

def add_to_history(text, model, voice, audio_base64, latency):
    """Add generated audio to history"""
    history_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'text': text,
        'model': model,
        'voice': voice,
        'audio_base64': audio_base64,
        'latency': latency
    }
    st.session_state.audio_history.insert(0, history_entry)  # Add to beginning

def clear_current_display():
    """Clear current audio displays"""
    st.session_state.current_spitch_audio = None
    st.session_state.current_awarri_audio = None

def display_audio_from_base64(audio_base64):
    """Display audio player from base64 string"""
    audio_bytes = base64.b64decode(audio_base64)
    st.audio(audio_bytes, format='audio/wav')

# Main UI
st.title("🎙️ Hausa Text-to-Speech Comparison")
st.markdown("Compare **Spitch AI** and **Awarri** TTS models for Hausa language")

st.divider()

# Input section
st.subheader("📝 Text Input")

text_input = st.text_area(
    "Enter Hausa text to convert to speech",
    height=120,
    max_chars=500,
    placeholder="Type your Hausa text here...",
    key="text_input"
)

char_count = len(text_input)
st.caption(f"Character count: {char_count}/500")

st.divider()

# Generation controls
st.subheader("⚙️ Generation Settings")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    voice_selection = st.selectbox(
        "Select Spitch Voice",
        options=["Hasan", "Amina", "Zainab", "Aliyu"],
        help="Voice selection only applies to Spitch AI"
    )

with col2:
    st.info("ℹ️ Awarri uses default voice")

with col3:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.text_input = ""
        clear_current_display()
        st.rerun()

st.divider()

# Generation buttons
st.subheader("🎵 Generate Audio")

col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("🔵 Generate with Spitch", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("Please enter text before generating")
        else:
            with st.spinner(f"Generating with Spitch ({voice_selection} voice)..."):
                audio_base64, latency = generate_spitch_audio(text_input, voice_selection)
                if audio_base64:
                    st.session_state.current_spitch_audio = {
                        'audio_base64': audio_base64,
                        'latency': latency,
                        'text': text_input,
                        'voice': voice_selection
                    }
                    st.success(f"Generated in {latency:.2f}s")

with col_btn2:
    if st.button("🔴 Generate with Awarri", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("Please enter text before generating")
        else:
            with st.spinner("Generating with Awarri..."):
                audio_base64, latency = generate_awarri_audio(text_input)
                if audio_base64:
                    st.session_state.current_awarri_audio = {
                        'audio_base64': audio_base64,
                        'latency': latency,
                        'text': text_input,
                        'voice': None
                    }
                    st.success(f"Generated in {latency:.2f}s")

st.divider()

# Display current generations
if st.session_state.current_spitch_audio or st.session_state.current_awarri_audio:
    st.subheader("🎧 Current Generation")
    
    col_play1, col_play2 = st.columns(2)
    
    with col_play1:
        st.markdown("### 🔴 Spitch AI")
        if st.session_state.current_spitch_audio:
            spitch_data = st.session_state.current_spitch_audio
            display_audio_from_base64(spitch_data['audio_base64'])
            st.metric("Latency", f"{spitch_data['latency']:.2f}s")
            st.caption(f"Voice: {spitch_data['voice']}")
            
            if st.button("💾 Save to History", key="save_spitch"):
                add_to_history(
                    spitch_data['text'],
                    "Spitch AI",
                    spitch_data['voice'],
                    spitch_data['audio_base64'],
                    spitch_data['latency']
                )
                st.success("Saved to history!")
                st.rerun()
        else:
            st.info("Generate with Spitch to see results here")
    
    with col_play2:
        st.markdown("### 🔵 Awarri")
        if st.session_state.current_awarri_audio:
            awarri_data = st.session_state.current_awarri_audio
            display_audio_from_base64(awarri_data['audio_base64'])
            st.metric("Latency", f"{awarri_data['latency']:.2f}s")
            st.caption("Voice: Default")
            
            if st.button("💾 Save to History", key="save_awarri"):
                add_to_history(
                    awarri_data['text'],
                    "Awarri",
                    "Default",
                    awarri_data['audio_base64'],
                    awarri_data['latency']
                )
                st.success("Saved to history!")
                st.rerun()
        else:
            st.info("Generate with Awarri to see results here")
    
    st.divider()

# History section
st.subheader("📜 Generation History")

if st.session_state.audio_history:
    st.caption(f"Total generations saved: {len(st.session_state.audio_history)}")
    
    for idx, entry in enumerate(st.session_state.audio_history):
        with st.expander(f"🎵 {entry['model']} - {entry['timestamp']}", expanded=(idx==0)):
            col_hist1, col_hist2 = st.columns([3, 1])
            
            with col_hist1:
                st.markdown(f"**Text:** {entry['text']}")
                st.markdown(f"**Model:** {entry['model']} | **Voice:** {entry['voice']} | **Latency:** {entry['latency']:.2f}s")
                
                # Audio player
                display_audio_from_base64(entry['audio_base64'])
            
            with col_hist2:
                st.markdown(f"**Time:**")
                st.caption(entry['timestamp'])
else:
    st.info("No audio generated yet. Generate some audio to see history here!")

st.divider()

# Footer
st.markdown("---")
st.caption("🎙️ Hausa TTS Comparison Tool | Spitch AI vs Awarri")