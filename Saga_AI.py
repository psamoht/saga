import streamlit as st
import openai
import locale
import speech_recognition as sr
import os
import tempfile
import wave
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder

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

# 🎙️ **Speech-to-Text Function (Fixed)**
def transcribe_audio(audio_path):
    st.audio(audio_path, format="audio/wav")
    st.info("🎧 This is your recorded/uploaded audio. If you hear only white noise, the file might be corrupted.")

    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio, language="de-DE" if lang == "de" else "en-US")
        return text
    except sr.UnknownValueError:
        st.warning("⚠️ Could not understand the audio. Try speaking more clearly.")
        return None
    except sr.RequestError:
        st.error("❌ Error: Could not connect to speech recognition service.")
        return None

# 🔊 **Text-to-Speech Function**
def text_to_speech(text):
    tts = gTTS(text, lang="de" if lang == "de" else "en")
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_audio.name)
    return temp_audio.name

# 📜 **UI Title**
st.title("🎙️ Saga – Be Part of the Story" if lang == "en" else "🎙️ Saga – Sei Teil der Geschichte")

# 🎤 **Microphone & File Upload (Fixed)**
st.info("📢 Speak a topic for your story or upload a voice file.")

# **Allow switching between microphone and file upload**
input_method = st.radio("Choose input method:", ["🎙 Microphone", "📤 Upload Audio File"])

audio_path = None

if input_method == "🎙 Microphone":
    audio_dict = mic_recorder(start_prompt="🎤 Speak Topic" if lang == "en" else "🎤 Thema sprechen")
    if audio_dict and "bytes" in audio_dict:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_dict["bytes"])
            temp_audio_path = temp_audio.name
        audio_path = temp_audio_path

elif input_method == "📤 Upload Audio File":
    uploaded_audio = st.file_uploader("📤 Upload a WAV/MP3 file", type=["wav", "mp3"])
    if uploaded_audio:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(uploaded_audio.read())
            temp_audio_path = temp_audio.name
        audio_path = temp_audio_path

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
