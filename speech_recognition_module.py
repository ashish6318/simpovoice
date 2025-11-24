"""
Speech recognition module for converting audio input to text.
Supports multiple recognition engines with configurable options.
"""

import speech_recognition as sr
import streamlit as st
from typing import Optional, Tuple

class SpeechToText:
    """Handle speech-to-text conversion using multiple engines"""
    
    def __init__(self, engine="google"):
        """
        Initialize the speech recognizer
        
        Args:
            engine: Recognition engine to use ('google', 'sphinx', 'whisper')
        """
        self.recognizer = sr.Recognizer()
        self.engine = engine
        
        # More sensitive settings for better detection
        self.recognizer.energy_threshold = 300  # Lower threshold = more sensitive
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.8  # How long to wait for pause (seconds)
    
    def listen_from_microphone(self, timeout=10, phrase_time_limit=15) -> Tuple[bool, str]:
        """
        Listen to microphone input and convert to text
        
        Args:
            timeout: Seconds to wait for speech to start
            phrase_time_limit: Maximum seconds for the phrase
            
        Returns:
            Tuple of (success: bool, text: str or error_message: str)
        """
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise - shorter duration
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for audio input
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                # Convert speech to text
                text = self._recognize_audio(audio)
                return True, text
                
        except sr.WaitTimeoutError:
            return False, "No speech detected. Please try again."
        except sr.UnknownValueError:
            return False, "Could not understand audio. Please speak clearly."
        except sr.RequestError as e:
            return False, f"Recognition service error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _recognize_audio(self, audio) -> str:
        """
        Recognize audio using the selected engine
        
        Args:
            audio: Audio data from microphone
            
        Returns:
            Recognized text
        """
        if self.engine == "google":
            # Google Speech Recognition (Free, online)
            return self.recognizer.recognize_google(audio)
        
        elif self.engine == "sphinx":
            # CMU Sphinx (Offline, less accurate)
            return self.recognizer.recognize_sphinx(audio)
        
        elif self.engine == "whisper":
            # OpenAI Whisper (requires openai-whisper package)
            # This would require additional setup
            return self.recognizer.recognize_whisper(audio)
        
        else:
            # Default to Google
            return self.recognizer.recognize_google(audio)
    
    def transcribe_audio_file(self, audio_file_path: str) -> Tuple[bool, str]:
        """
        Transcribe an audio file to text
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Tuple of (success: bool, text: str or error_message: str)
        """
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
                text = self._recognize_audio(audio)
                return True, text
        except Exception as e:
            return False, f"Error transcribing file: {str(e)}"


def test_microphone():
    """Test if microphone is available"""
    try:
        with sr.Microphone() as source:
            return True, "Microphone is working!"
    except Exception as e:
        return False, f"Microphone error: {str(e)}"


# Streamlit-specific speech input component
def streamlit_speech_input(key="speech_input"):
    """
    Create a Streamlit button for speech input
    
    Returns:
        Recognized text or None
    """
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("🎤 Speak", key=key, help="Click and speak your query"):
            return "RECORDING"
    
    with col2:
        st.caption("Click the microphone button and speak your query")
    
    return None


if __name__ == "__main__":
    # Test the speech recognition
    print("Testing Speech Recognition Module...")
    print("-" * 50)
    
    # Test microphone availability
    success, message = test_microphone()
    print(f"Microphone Test: {message}")
    
    if success:
        # Test speech recognition
        stt = SpeechToText(engine="google")
        print("\nSpeak something (you have 5 seconds)...")
        success, result = stt.listen_from_microphone(timeout=5)
        
        if success:
            print(f"You said: {result}")
        else:
            print(f"Error: {result}")
    
    print("-" * 50)
