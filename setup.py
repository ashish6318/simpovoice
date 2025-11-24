"""
Setup and initialization script for SimploVoice.
Validates environment, initializes database, and checks dependencies.
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Verify Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def check_dependencies():
    """Check if all required packages are installed"""
    required = [
        'streamlit',
        'groq',
        'edge_tts',
        'dotenv',
        'speech_recognition',
        'sounddevice',
        'soundfile',
        'numpy'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✓ All dependencies installed")
    return True


def setup_environment():
    """Create .env file if it doesn't exist"""
    env_path = Path('.env')
    template_path = Path('.env.template')
    
    if not env_path.exists() and template_path.exists():
        print("\n📝 Creating .env file from template...")
        env_path.write_text(template_path.read_text())
        print("✓ .env file created")
        print("⚠️  Please edit .env and add your GROQ_API_KEY")
        return False
    elif not env_path.exists():
        print("\n⚠️  .env file not found")
        print("Create one with GROQ_API_KEY=your_key_here")
        return False
    
    # Load and validate environment
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('GROQ_API_KEY', '')
    if not api_key or api_key == 'your_groq_api_key_here':
        print("⚠️  GROQ_API_KEY not set in .env file")
        print("AI features will be disabled (rule-based responses only)")
        return True
    
    print("✓ Environment configured")
    return True


def initialize_database():
    """Initialize database with sample data"""
    try:
        from database import init_db
        init_db()
        print("✓ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def test_speech_recognition():
    """Test if microphone is accessible"""
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        mic_list = sr.Microphone.list_microphone_names()
        print(f"✓ Found {len(mic_list)} microphone(s)")
        return True
    except Exception as e:
        print(f"⚠️  Microphone test failed: {e}")
        print("Speech recognition may not work properly")
        return True  # Non-fatal


def run_setup():
    """Run all setup checks"""
    print("=" * 60)
    print("SimploVoice Setup & Configuration Check")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment", setup_environment),
        ("Database", initialize_database),
        ("Speech Recognition", test_speech_recognition),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        result = check_func()
        results.append(result)
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ Setup complete! You can now run: streamlit run app.py")
    else:
        print("⚠️  Setup completed with warnings. Please review above.")
    print("=" * 60)


if __name__ == "__main__":
    run_setup()
