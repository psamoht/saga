import streamlit as st
import openai
import locale
import speech_recognition as sr
import os
import tempfile
import wave
from gtts import gTTS
from pydub import AudioSegment  # 🔥 Fixes MP3-to-WAV conversion issue
import sounddevice as sd  # 🔥 Alternative audio recording method
import numpy as np

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

# 🎙 **Alternative Voice Recorder (Replaces mic_recorder)**
def record_audio():
    """ Record audio using sounddevice and return as WAV. """
    st.info("🎤 Recording... Speak now!")
    duration = 5  # seconds
    fs = 44100  # Sample rate
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
    sd.wait()  # Wait until recording is finished

    # Save as WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio_path = temp_audio.name
        with wave.open(temp_audio_path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(fs)
            wav_file.writeframes(recording.tobytes())

    return temp_audio_path

# 🎙️ **Speech-to-Text Function (Fixed)**
def transcribe_audio(audio_path):
    """ Converts speech to text from an audio file. """
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        st.error("❌ Error: Audio file is empty or not recorded correctly.")
        return None

    # Play back audio to debug
    st.audio(audio_path, format="audio/wav")
    st.info("🎧 Playing back recorded/uploaded audio. If silent or noisy, check your microphone.")

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

# 🎤 **Microphone & File Upload (Fixed)**
st.info("📢 Speak a topic for your story or upload a voice file.")

# **Allow switching between microphone and file upload**
input_method = st.radio("Choose input method:", ["🎙 Microphone", "📤 Upload Audio File"])

audio_path = None

if input_method == "🎙 Microphone":
    if st.button("🎤 Start Recording"):
        audio_path = record_audio()
        st.success("✅ Recording finished! Now processing...")

elif input_method == "📤 Upload Audio File":
    uploaded_audio = st.file_uploader("📤 Upload a WAV/MP3 file", type=["wav", "mp3"])
    if uploaded_audio:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio_path = temp_audio.name
            file_extension = uploaded_audio.name.split(".")[-1].lower()

            # Convert MP3 to WAV if necessary
            if file_extension == "mp3":
                audio = AudioSegment.from_file(uploaded_audio, format="mp3")
                audio.export(temp_audio_path, format="wav")
            else:
                temp_audio.write(uploaded_audio.read())

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
