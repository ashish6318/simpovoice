"""
Text-to-Speech module using Microsoft Edge TTS.
Provides speech synthesis for bot responses with configurable voice options.
"""

import edge_tts
import asyncio
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import tempfile


class TextToSpeech:
    """
    Production-grade TTS engine using Microsoft Edge TTS.
    Handles audio generation, file management, and cleanup.
    """
    
    def __init__(self, voice: str = "en-US-AriaNeural", rate: str = "+0%", pitch: str = "+0Hz"):
        """
        Initialize TTS engine.
        
        Args:
            voice: Voice identifier (e.g., 'en-US-AriaNeural', 'en-US-GuyNeural')
            rate: Speech rate adjustment (e.g., '+10%', '-10%')
            pitch: Pitch adjustment (e.g., '+5Hz', '-5Hz')
        """
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.audio_dir = Path("audio_cache")
        self.audio_dir.mkdir(exist_ok=True)
        self._cleanup_old_files()
    
    async def _generate_audio(self, text: str, output_path: str) -> bool:
        """
        Generate audio file from text asynchronously.
        
        Args:
            text: Text to convert to speech
            output_path: Path where audio file will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch
            )
            await communicate.save(output_path)
            return True
        except Exception as e:
            print(f"TTS generation error: {e}")
            return False
    
    def text_to_speech(self, text: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Convert text to speech and save as audio file.
        
        Args:
            text: Text to convert
            filename: Optional custom filename (without extension)
            
        Returns:
            Path to generated audio file, or None if failed
        """
        if not text or not text.strip():
            return None
        
        # Generate filename
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tts_{timestamp}"
        
        output_path = self.audio_dir / f"{filename}.mp3"
        
        # Run async generation in sync context
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(self._generate_audio(text, str(output_path)))
            loop.close()
            
            if success and output_path.exists():
                return str(output_path)
            return None
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    def _cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old audio files to prevent disk space issues.
        
        Args:
            max_age_hours: Delete files older than this many hours
        """
        if not self.audio_dir.exists():
            return
        
        current_time = datetime.now().timestamp()
        max_age_seconds = max_age_hours * 3600
        
        for audio_file in self.audio_dir.glob("*.mp3"):
            try:
                file_age = current_time - audio_file.stat().st_mtime
                if file_age > max_age_seconds:
                    audio_file.unlink()
            except Exception:
                pass
    
    def cleanup_all(self):
        """Remove all cached audio files"""
        for audio_file in self.audio_dir.glob("*.mp3"):
            try:
                audio_file.unlink()
            except Exception:
                pass
    
    @staticmethod
    async def get_available_voices():
        """Get list of available voices"""
        try:
            voices = await edge_tts.list_voices()
            return voices
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return []
    
    @staticmethod
    def list_voices():
        """Synchronous wrapper to list available voices"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        voices = loop.run_until_complete(TextToSpeech.get_available_voices())
        loop.close()
        return voices


# Voice presets for different use cases
VOICE_PRESETS = {
    'female_professional': {
        'voice': 'en-US-AriaNeural',
        'rate': '+0%',
        'pitch': '+0Hz',
        'description': 'Professional female voice (default)'
    },
    'male_professional': {
        'voice': 'en-US-GuyNeural',
        'rate': '+0%',
        'pitch': '+0Hz',
        'description': 'Professional male voice'
    },
    'female_friendly': {
        'voice': 'en-US-JennyNeural',
        'rate': '+5%',
        'pitch': '+2Hz',
        'description': 'Friendly female voice'
    },
    'male_calm': {
        'voice': 'en-US-EricNeural',
        'rate': '-5%',
        'pitch': '-2Hz',
        'description': 'Calm male voice'
    },
}


def get_tts_engine(preset: str = 'female_professional') -> TextToSpeech:
    """
    Factory function to create TTS engine with preset configuration.
    
    Args:
        preset: Voice preset name from VOICE_PRESETS
        
    Returns:
        Configured TextToSpeech instance
    """
    config = VOICE_PRESETS.get(preset, VOICE_PRESETS['female_professional'])
    return TextToSpeech(
        voice=config['voice'],
        rate=config['rate'],
        pitch=config['pitch']
    )


# Test function
if __name__ == "__main__":
    print("Testing Text-to-Speech Module...")
    
    # Test TTS generation
    tts = get_tts_engine('female_professional')
    test_text = "Hello! I'm here to help you find the perfect room at the best price."
    
    print(f"Converting text to speech: {test_text}")
    audio_path = tts.text_to_speech(test_text, "test_output")
    
    if audio_path:
        print(f"✓ Audio generated successfully: {audio_path}")
        print(f"File size: {os.path.getsize(audio_path)} bytes")
    else:
        print("✗ Audio generation failed")
    
    # List available voices
    print("\nFetching available voices...")
    voices = tts.list_voices()
    if voices:
        print(f"✓ Found {len(voices)} voices")
        print("\nEnglish voices:")
        for voice in voices[:5]:  # Show first 5
            if 'en-' in voice['ShortName']:
                print(f"  - {voice['ShortName']}: {voice['Gender']}")
    
    print("\nAvailable presets:")
    for preset_name, preset_config in VOICE_PRESETS.items():
        print(f"  - {preset_name}: {preset_config['description']}")
