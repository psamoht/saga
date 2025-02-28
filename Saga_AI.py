import streamlit as st
import openai
import locale
import speech_recognition as sr
import os
import tempfile
import wave
import io
from gtts import gTTS

# OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🌍 Detect system language for default selection
user_locale = locale.getlocale()[0]  
default_lang = "de" if user_locale and "de" in user_locale else "en"

# 🌐 Language Selection Dropdown
lang_options = {"English": "en", "Deutsch": "de"}
selected_lang = st.selectbox("🌍 Select Language / Sprache wählen:", list(lang_options.keys()), index=0 if default_lang == "en" else 1)
lang = lang_options[selected_lang]

# 🏗 **Session State Initialization**
if "story" not in st.session_state:
    st.session_state.story = ""
if "history" not in st.session_state:
    st.session_state.history = []
if "user_decision" not in st.session_state:
    st.session_state.user_decision = None
if "topic" not in st.session_state:
    st.session_state.topic = None
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = None
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None
if "story_generated" not in st.session_state:
    st.session_state.story_generated = False  # 🚀 Prevents infinite loop

# 🎙️ **Ensure WAV File is Valid**
def validate_wav(audio_path):
    """ Ensures the uploaded WAV file is valid and playable. """
    try:
        with wave.open(audio_path, "rb") as wav_file:
            params = wav_file.getparams()
            num_channels, sampwidth, framerate, nframes = params[:4]
            
            # ✅ Validate PCM WAV format
            if sampwidth != 2:
                st.error("❌ Error: WAV file must be 16-bit PCM.")
                return None
            if num_channels not in [1, 2]:
                st.error("❌ Error: WAV file must be mono or stereo.")
                return None
            if framerate < 8000 or framerate > 48000:
                st.error("❌ Error: WAV file sample rate must be between 8kHz and 48kHz.")
                return None
            
            return audio_path

    except Exception as e:
        st.error(f"❌ WAV processing error: {str(e)}")
        return None

# 🎙️ **Speech-to-Text Function**
def transcribe_audio(audio_path):
    """ Converts speech to text from a WAV file. """
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        st.error("❌ Error: Audio file is empty or not recorded correctly.")
        return None

    # Ensure valid WAV file
    valid_wav_path = validate_wav(audio_path)
    if not valid_wav_path:
        return None

    # 🔊 Play back audio to debug
    st.audio(valid_wav_path, format="audio/wav")
    st.info("🎧 Playing back processed audio.")

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(valid_wav_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language="de-DE" if lang == "de" else "en-US")

        # Store transcribed text in session state
        st.session_state.transcribed_text = text
        return text
    except sr.UnknownValueError:
        st.warning("⚠️ Could not understand the audio. Try speaking more clearly.")
        return None
    except sr.RequestError:
        st.error("❌ Error: Could not connect to speech recognition service.")
        return None
    except Exception as e:
        st.error(f"❌ Audio processing error: {str(e)}")
        return None

# 🔊 **Text-to-Speech Function**
def text_to_speech(text):
    """ Generates and saves speech audio from text using gTTS. """
    try:
        tts = gTTS(text, lang="de" if lang == "de" else "en")
        temp_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        tts.save(temp_audio_path)
        return temp_audio_path
    except Exception as e:
        st.error(f"❌ TTS Error: {str(e)}")
        return None

# 📜 **UI Title**
st.title("🎙️ Saga – Be Part of the Story" if lang == "en" else "🎙️ Saga – Sei Teil der Geschichte")

# 🎤 **File Upload**
st.info("📢 Upload a voice file to start your story.")

uploaded_audio = st.file_uploader("📤 Upload a WAV file", type=["wav"])

def process_uploaded_audio(audio_file):
    """ Processes uploaded WAV files and ensures they are playable. """
    try:
        temp_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name

        # Save uploaded file
        with open(temp_audio_path, "wb") as f:
            f.write(audio_file.read())

        # ✅ Ensure valid WAV format
        return validate_wav(temp_audio_path)

    except Exception as e:
        st.error(f"❌ Audio processing error: {str(e)}")
        return None

audio_path = None

if uploaded_audio and not st.session_state.transcribed_text:
    audio_path = process_uploaded_audio(uploaded_audio)

    # 🔎 **Process Audio if Available**
    if audio_path:
        topic = transcribe_audio(audio_path)
        if topic:
            st.success(f"✅ You said: {topic}")
            st.session_state.topic = topic
            st.session_state.story = f"Generating a story about {topic}..."
            st.session_state.story_generated = False  # 🚀 Reset flag
            st.rerun()

# 🌟 **Generate Initial Story**
if st.session_state.topic and not st.session_state.story_generated:
    topic = st.session_state.topic
    try:
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

        # Save the story and reset state
        st.session_state.story = response.choices[0].message.content
        st.session_state.history.append(st.session_state.story)

        # Generate speech audio
        audio_path = text_to_speech(st.session_state.story)
        if audio_path:
            st.session_state.audio_file = audio_path

        st.session_state.transcribed_text = None
        st.session_state.story_generated = True  # 🚀 Prevents infinite loop
        #st.rerun()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# 📖 **Play and Display Story**
if st.session_state.story and st.session_state.audio_file:
    st.markdown(f"<p style='font-size:18px;'>{st.session_state.story}</p>", unsafe_allow_html=True)
    st.audio(st.session_state.audio_file, format="audio/mp3")
