import streamlit as st
import openai
import locale
import speech_recognition as sr
import os
import tempfile
import wave
import io
from gtts import gTTS
from pydub import AudioSegment  # ✅ Convert WAV to PCM WAV if needed

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

# 🎙️ **Ensure WAV is Proper PCM Format**
def ensure_pcm_wav(audio_path):
    """ Converts non-PCM WAV files to proper PCM format. """
    try:
        with wave.open(audio_path, "rb") as wav_file:
            sample_width = wav_file.getsampwidth()
            channels = wav_file.getnchannels()
            frame_rate = wav_file.getframerate()
        
        # ✅ If file is already PCM WAV, return it
        if sample_width == 2 and channels in [1, 2]:
            return audio_path
        
        # 🔄 Convert to PCM WAV if needed
        audio = AudioSegment.from_wav(audio_path)
        pcm_wav_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        audio.export(pcm_wav_path, format="wav", parameters=["-acodec", "pcm_s16le"])
        return pcm_wav_path

    except Exception as e:
        st.error(f"❌ WAV processing error: {str(e)}")
        return None

# 🎙️ **Speech-to-Text Function**
def transcribe_audio(audio_path):
    """ Converts speech to text from an audio file. """
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        st.error("❌ Error: Audio file is empty or not recorded correctly.")
        return None

    # Ensure proper PCM WAV format
    pcm_wav_path = ensure_pcm_wav(audio_path)
    if not pcm_wav_path:
        return None

    # Play back audio to debug
    st.audio(pcm_wav_path, format="audio/wav")
    st.info("🎧 Playing back processed audio.")

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(pcm_wav_path) as source:
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

uploaded_audio = st.file_uploader("📤 Upload a WAV file (PCM only)", type=["wav"])

def process_uploaded_audio(audio_file):
    """ Processes uploaded WAV files and ensures correct PCM format. """
    try:
        temp_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name

        # Save uploaded file
        with open(temp_audio_path, "wb") as f:
            f.write(audio_file.read())

        # ✅ Ensure PCM WAV format
        return ensure_pcm_wav(temp_audio_path)

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
