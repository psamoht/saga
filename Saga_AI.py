# 🎯 Import necessary libraries
import streamlit as st  # 📌 Streamlit for UI
import openai  # 📌 OpenAI API for generating stories
import locale  # 📌 Locale for detecting system language
import speech_recognition as sr  # 📌 Speech-to-text conversion
import os  # 📌 File operations
import tempfile  # 📌 Temporary file handling
import wave  # 📌 WAV audio processing
import io  # 📌 Input/output operations
from gtts import gTTS  # 📌 Google Text-to-Speech for audio playback

# 🔑 OpenAI API Key (must be set in Streamlit secrets)
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🌍 Detect system language for default selection
user_locale = locale.getlocale()[0]  # Get user's locale settings
default_lang = "de" if user_locale and "de" in user_locale else "en"  # Set default language

# 🌐 Language Selection Dropdown
lang_options = {"English": "en", "Deutsch": "de"}  # Define language choices
selected_lang = st.selectbox("🌍 Select Language / Sprache wählen:", list(lang_options.keys()), 
                             index=0 if default_lang == "en" else 1)  # Default to detected language
lang = lang_options[selected_lang]  # Store selected language

# 🏗 **Initialize Session State Variables** (Persistent between reruns)
if "story" not in st.session_state:
    st.session_state.story = ""  # 📌 Stores the generated story
if "history" not in st.session_state:
    st.session_state.history = []  # 📌 Stores previous story sections
if "user_decision" not in st.session_state:
    st.session_state.user_decision = None  # 📌 Stores last user input
if "topic" not in st.session_state:
    st.session_state.topic = None  # 📌 Stores transcribed topic
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = None  # 📌 Stores last transcribed text
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None  # 📌 Stores generated TTS file
if "story_generated" not in st.session_state:
    st.session_state.story_generated = False  # 📌 Prevents infinite loop

# 🎙️ **Function to Validate WAV Files**
def validate_wav(audio_path):
    """Ensures the uploaded WAV file is valid and playable."""
    try:
        with wave.open(audio_path, "rb") as wav_file:
            params = wav_file.getparams()
            num_channels, sampwidth, framerate, nframes = params[:4]

            # ✅ Check that the file is a proper 16-bit PCM WAV file
            if sampwidth != 2:
                st.error("❌ Error: WAV file must be 16-bit PCM.")
                return None
            if num_channels not in [1, 2]:
                st.error("❌ Error: WAV file must be mono or stereo.")
                return None
            if framerate < 8000 or framerate > 48000:
                st.error("❌ Error: WAV file sample rate must be between 8kHz and 48kHz.")
                return None
            
            return audio_path  # ✅ If everything is valid, return the file path

    except Exception as e:
        st.error(f"❌ WAV processing error: {str(e)}")
        return None

# 🌟 **Speech-to-Text Function**
def transcribe_audio(audio_path):
    """Converts speech to text from a WAV file."""
    valid_wav_path = validate_wav(audio_path)  # Ensure it's a valid WAV file
    if not valid_wav_path:
        return None

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(valid_wav_path) as source:
            audio = recognizer.record(source)  # Capture entire audio file
        text = recognizer.recognize_google(audio, language="de-DE" if lang == "de" else "en-US")

        st.session_state.transcribed_text = text  # ✅ Store transcribed text in session state
        return text  # Return the text

    except Exception as e:
        st.error(f"❌ Audio processing error: {str(e)}")
        return None

# 🔊 **Text-to-Speech Function**
def text_to_speech(text):
    """Converts text to speech using gTTS and saves as MP3."""
    try:
        tts = gTTS(text, lang="de" if lang == "de" else "en")
        temp_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        tts.save(temp_audio_path)
        return temp_audio_path
    except Exception as e:
        st.error(f"❌ TTS Error: {str(e)}")
        return None

# 📜 **User Interface**
st.title("🎙️ Saga – Be Part of the Story" if lang == "en" else "🎙️ Saga – Sei Teil der Geschichte")

uploaded_audio = st.file_uploader("📤 Upload a WAV file", type=["wav"])

if uploaded_audio and not st.session_state.transcribed_text:
    audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    with open(audio_path, "wb") as f:
        f.write(uploaded_audio.read())

    topic = transcribe_audio(audio_path)
    if topic:
        st.session_state.topic = topic
        st.session_state.story_generated = False  # ✅ Reset generation flag
        #st.rerun()  # 🔄 **Triggers app restart** to load the story

# 🌟 **Story Generation**
if st.session_state.topic and not st.session_state.story_generated:
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
                {"role": "system", "content": f"""Create a fun, engaging children's story for a 5-year-old in {lang}. 
                Each section should be around 200 words long. 
                The story should flow naturally and lead to a decision point where the main character needs to decide what to do next. 
                This decision point should be obvious but not limited to two specific options.
                It should feel open-ended, allowing different choices from the reader."""},
                {"role": "user", "content": f"Write a children's story about {topic}. "
                                            f"Ensure that the story section is about 200 words long and ends at an open-ended decision point."}
            ]
    )
    st.session_state.story = response.choices[0].message.content
    st.session_state.story_generated = True  # ✅ Prevents infinite rerun

# 📖 **Display Story**
if st.session_state.story:
    st.markdown(st.session_state.story)
