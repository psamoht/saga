import streamlit as st
import openai
import locale
import speech_recognition as sr
import os
import tempfile
import wave
import io
from gtts import gTTS
from mutagen.mp3 import MP3  # ✅ Read MP3 duration without conversion

# OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🌍 Detect system language for default selection
user_locale = locale.getlocale()[0]  
default_lang = "de" if user_locale and "de" in user_locale else "en"

# 🌐 Language Selection Dropdown
lang_options = {"English": "en", "Deutsch": "de"}
selected_lang = st.selectbox("🌍 Select Language / Sprache wählen:", list(lang_options.keys()), index=0 if default_lang == "en" else 1)
lang = lang_options[selected_lang]

# 🏗 Session State Initialization
if "story" not in st.session_state:
    st.session_state.story = ""
if "history" not in st.session_state:
    st.session_state.history = []
if "user_decision" not in st.session_state:
    st.session_state.user_decision = None
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None

# 🎙️ **Speech-to-Text Function**
def transcribe_audio(audio_path):
    """ Converts speech to text from an audio file. """
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        st.error("❌ Error: Audio file is empty or not recorded correctly.")
        return None

    # Play back audio to debug
    st.audio(audio_path, format="audio/wav")
    st.info("🎧 Playing back uploaded audio. If silent, file processing failed.")

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language="de-DE" if lang == "de" else "en-US")
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
    tts = gTTS(text, lang="de" if lang == "de" else "en")
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_audio.name)
    return temp_audio.name

# 📜 **UI Title**
st.title("🎙️ Saga – Be Part of the Story" if lang == "en" else "🎙️ Saga – Sei Teil der Geschichte")

# 🎤 **File Upload**
st.info("📢 Upload a voice file to start your story.")

uploaded_audio = st.file_uploader("📤 Upload a WAV/MP3 file", type=["wav", "mp3"])

def process_uploaded_audio(audio_file):
    """ Processes uploaded WAV or MP3 files correctly without conversion. """
    try:
        file_extension = audio_file.name.split(".")[-1].lower()
        temp_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}").name

        # Save uploaded file
        with open(temp_audio_path, "wb") as f:
            f.write(audio_file.read())

        # ✅ Directly process WAV
        if file_extension == "wav":
            return temp_audio_path

        # ✅ Process MP3 without conversion
        elif file_extension == "mp3":
            try:
                audio = MP3(temp_audio_path)  # Read MP3 duration (ensures file is valid)
                if audio.info.length < 1:
                    st.error("❌ Error: MP3 file is too short or empty.")
                    return None
                return temp_audio_path
            except Exception as e:
                st.error(f"❌ Error processing MP3: {str(e)}")
                return None

        else:
            st.error("❌ Unsupported file format.")
            return None

    except Exception as e:
        st.error(f"❌ Audio processing error: {str(e)}")
        return None

audio_path = None

if uploaded_audio:
    audio_path = process_uploaded_audio(uploaded_audio)

    # 🔎 **Process Audio if Available**
    if audio_path:
        topic = transcribe_audio(audio_path)
        if topic:
            st.success(f"✅ You said: {topic}")
            st.session_state.story = f"Generating a story about {topic}..."
            st.rerun()

# 🌟 **Generate Initial Story**
if st.session_state.story and st.session_state.story.startswith("Generating a story"):
    topic = st.session_state.story.replace("Generating a story about ", "").strip()
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Create a fun, engaging children's story for a 5-year-old in {lang}. "
                                              f"Each section should be around 200 words long. "
                                              f"The story should flow naturally and lead to a decision point where the main character needs to decide what to do next. "
                                              f"This decision point should be obvious but not limited to two specific options. "
                                              f"It should feel open-ended, allowing different choices from the reader."},
                {"role": "user", "content": f"Write a children's story about {topic}. "
                                            f"Ensure that the story section is about 200 words long and ends at an open-ended decision point."}
            ]
        )

        # Save the story and reset state
        st.session_state.story = response.choices[0].message.content
        st.session_state.history.append(st.session_state.story)

        # Convert story to speech
        st.session_state.audio_file = text_to_speech(st.session_state.story)
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# 📖 **Play and Display Story**
if st.session_state.story and st.session_state.audio_file:
    st.markdown(f"<p style='font-size:18px;'>{st.session_state.story}</p>", unsafe_allow_html=True)
    st.audio(st.session_state.audio_file, format="audio/mp3")
