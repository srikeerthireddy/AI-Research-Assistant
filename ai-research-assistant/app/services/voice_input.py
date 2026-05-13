"""
Voice Input Module for AI Research Assistant
Enables voice-to-text input and processing
"""
import streamlit as st
try:
    import speech_recognition as sr
    from pydub import AudioSegment
    import io
    HAS_SPEECH = True
except ImportError:
    HAS_SPEECH = False

def get_voice_input():
    """
    Capture voice input from user microphone
    Returns text transcription
    """
    if not HAS_SPEECH:
        st.warning("⚠️ Voice module not installed. Install with: pip install SpeechRecognition pydub")
        return None
    
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🎤 Listening... Please speak now")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)
            
            try:
                text = recognizer.recognize_google(audio)
                st.success(f"✅ Transcribed: {text}")
                return text
            except sr.UnknownValueError:
                st.error("❌ Could not understand audio. Please try again.")
                return None
            except sr.RequestError:
                st.error("❌ Speech recognition service error.")
                return None
    except Exception as e:
        st.error(f"❌ Microphone error: {str(e)}")
        return None

def process_audio_file(audio_file):
    """
    Process uploaded audio file
    Supports: MP3, WAV, OGG, FLAC
    """
    if not HAS_SPEECH:
        st.warning("⚠️ Voice module not installed.")
        return None
    
    try:
        recognizer = sr.Recognizer()
        
        # Convert to WAV if needed
        audio = AudioSegment.from_file(io.BytesIO(audio_file.getvalue()))
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)
        
        # Recognize speech
        audio_data = sr.AudioData(wav_io.read(), 16000, 2)
        text = recognizer.recognize_google(audio_data)
        return text
    except Exception as e:
        st.error(f"❌ Audio processing error: {str(e)}")
        return None

def add_voice_input_component():
    """
    Add voice input UI component to Streamlit page
    """
    st.markdown("### 🎤 Voice Input")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎙️ Record Voice Input", use_container_width=True):
            voice_text = get_voice_input()
            if voice_text:
                return voice_text
    
    with col2:
        audio_file = st.file_uploader(
            "Or upload audio file",
            type=["mp3", "wav", "ogg", "flac"],
            label_visibility="collapsed"
        )
        if audio_file:
            voice_text = process_audio_file(audio_file)
            if voice_text:
                return voice_text
    
    return None
