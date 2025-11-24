"""
Main Streamlit application for voice-enabled hotel booking assistant.
Integrates speech recognition, AI processing, and text-to-speech.
"""

import streamlit as st
from dotenv import load_dotenv
from brain import get_agent_response
from speech_recognition_module import SpeechToText, test_microphone
from nlu_processor import analyze_query
from config import config
from tts_module import get_tts_engine
import os
import time

# Load environment variables
load_dotenv()

# Initialize database on first run
from database import init_db
if not os.path.exists(config.database.db_path):
    init_db()

# Page configuration
st.set_page_config(
    page_title="Simplotel Voice Assistant",
    page_icon="🏨",
    layout="wide"
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "total_savings" not in st.session_state:
    st.session_state.total_savings = 0

if "stt_engine" not in st.session_state:
    st.session_state.stt_engine = None

if "listening" not in st.session_state:
    st.session_state.listening = False

if "last_nlu" not in st.session_state:
    st.session_state.last_nlu = None

if "tts_engine" not in st.session_state:
    st.session_state.tts_engine = get_tts_engine(config.tts.voice_preset)

# Main title
st.title("🏨 Simplotel Voice Assistant")
st.markdown("*Your personal hotel booking agent - Save 15% by booking directly!*")

# Sidebar with analytics and speech settings
with st.sidebar:
    st.header("📊 Analytics Dashboard")
    st.caption("*Track performance metrics*")
    
    from database import get_analytics
    analytics = get_analytics()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("User Queries", analytics['total_queries'])
        st.metric("Response Time", f"{analytics['avg_response_time_ms']}ms")
    with col2:
        st.metric("Success Rate", f"{100 - analytics['error_rate']:.1f}%")
        st.metric("Avg Confidence", f"{analytics['avg_confidence']:.0%}")
    
    st.divider()
    
    st.header("� Booking Stats")
    st.metric(
        label="Money Saved by Direct Booking",
        value="₹12,500",
        delta="15% discount"
    )
    
    st.divider()
    st.info("**Direct Booking Benefits:**\n- 15% cheaper than OTA prices\n- No hidden fees\n- Best rate guarantee\n- Direct customer support")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Play audio for assistant messages
        if message["role"] == "assistant" and "audio_file" in message:
            if os.path.exists(message["audio_file"]):
                with open(message["audio_file"], "rb") as audio_file:
                    st.audio(audio_file.read(), format="audio/mp3")

# Voice input using Streamlit component
import streamlit.components.v1 as components

# Web Speech API Integration
voice_html = """
<div style="margin-bottom: 20px;">
    <button id="voiceBtn" 
            style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; 
                   border: none; 
                   padding: 12px 24px; 
                   font-size: 16px; 
                   border-radius: 8px; 
                   cursor: pointer; 
                   font-weight: bold;
                   box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        🎤 Click to Speak
    </button>
    <span id="status" style="margin-left: 15px; font-size: 14px; color: #666;"></span>
</div>

<script>
const voiceBtn = document.getElementById('voiceBtn');
const statusEl = document.getElementById('status');
let recognition;
let isListening = false;

voiceBtn.addEventListener('click', function() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        statusEl.textContent = '❌ Speech recognition not supported. Use Chrome or Edge.';
        statusEl.style.color = '#d32f2f';
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;
    
    recognition.onstart = function() {
        isListening = true;
        statusEl.textContent = '🎤 Listening... Speak now!';
        statusEl.style.color = '#4caf50';
        voiceBtn.style.background = 'linear-gradient(135deg, #d32f2f 0%, #c62828 100%)';
        voiceBtn.textContent = '⏹️ Stop';
    };
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        statusEl.textContent = '✅ Got it: "' + transcript + '"';
        statusEl.style.color = '#4caf50';
        
        // Try to find and fill the chat input
        const chatInput = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
        if (chatInput) {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
            nativeInputValueSetter.call(chatInput, transcript);
            
            const inputEvent = new Event('input', { bubbles: true});
            chatInput.dispatchEvent(inputEvent);
            chatInput.focus();
        }
    };
    
    recognition.onerror = function(event) {
        if (event.error === 'no-speech') {
            statusEl.textContent = '❌ No speech detected. Try again.';
        } else if (event.error === 'not-allowed') {
            statusEl.textContent = '❌ Microphone blocked. Allow in browser settings.';
        } else {
            statusEl.textContent = '❌ Error: ' + event.error;
        }
        statusEl.style.color = '#d32f2f';
        resetButton();
    };
    
    recognition.onend = function() {
        isListening = false;
        resetButton();
    };
    
    function resetButton() {
        voiceBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        voiceBtn.textContent = '🎤 Click to Speak';
    }
    
    if (isListening && recognition) {
        recognition.stop();
    } else {
        recognition.start();
    }
});
</script>
"""

components.html(voice_html, height=80)

# Text input
prompt = st.chat_input("Or type your question here...")

# Process the input (speech or text)
if prompt:
    # NLU Analysis
    nlu_analysis = analyze_query(prompt)
    st.session_state.last_nlu = {
        'intent': nlu_analysis['intent'],
        'confidence': nlu_analysis['intent_confidence'],
        'entities': nlu_analysis['entities']
    }
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_agent_response(prompt)
            st.markdown(response)
            
            # Generate audio (Text-to-Speech)
            audio_file = None
            if config.tts.enabled:
                try:
                    tts_filename = f"response_{len(st.session_state.messages)}"
                    audio_path = st.session_state.tts_engine.text_to_speech(response, tts_filename)
                    
                    if audio_path and os.path.exists(audio_path):
                        with open(audio_path, "rb") as af:
                            st.audio(af.read(), format="audio/mp3")
                        audio_file = audio_path
                except Exception as e:
                    st.warning(f"⚠️ Audio generation failed: {str(e)}")
                    audio_file = None
    
    # Add assistant response to chat
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "audio_file": audio_file
    })
    
    # Rerun to update chat
    st.rerun()

# Footer
st.divider()
st.caption("Powered by Groq AI + Edge TTS | Built for Simplotel Internship Assignment")
