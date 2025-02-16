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
user_locale = locale.getlocale()[0]  # Avoids deprecated `getdefaultlocale()`
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

# 🎙️ Speech-to-Text Function (With Debugging)
def transcribe_audio(audio_dict):
    if not audio_dict or "bytes" not in audio_dict:
        st.warning("⚠️ No valid audio detected. Please try speaking again.")
        return None

    audio_bytes = audio_dict["bytes"]  # Extract raw audio data

    # Save audio as a proper WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio_path = temp_audio.name
        with wave.open(temp_audio_path, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono audio
            wav_file.setsampwidth(2)  # 16-bit audio
            wav_file.setframerate(44100)  # Sample rate
            wav_file.writeframes(audio_bytes)

    # 🎧 Debug: Allow user to play back their own recording
    st.audio(temp_audio_path, format="audio/wav")
    st.info("🎧 This is your recorded audio. If you hear nothing, your microphone is not working correctly.")

    # Process audio with SpeechRecognition
    recognizer = sr.Recognizer()
    with sr.AudioFile(temp_audio_path) as source:
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
    finally:
        os.remove(temp_audio_path)  # Clean up the temp file

# 🔊 Text-to-Speech Function
def text_to_speech(text):
    tts = gTTS(text, lang="de" if lang == "de" else "en")
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_audio.name)
    return temp_audio.name

# 📜 UI Title
st.title("🎙️ Saga – Be Part of the Story" if lang == "en" else "🎙️ Saga – Sei Teil der Geschichte")

# 🎤 Welcome Message & Voice Input for Topic (With Mobile Support)
st.info("📢 Speak a topic for your story.")

if st.session_state.story == "":
    audio_dict = None

    # 🔹 Check if user is on mobile
    if st.session_state.get("is_mobile", None) is None:
        st.session_state.is_mobile = st.file_uploader("📱 Upload an audio file if the microphone does not work.", type=["wav", "mp3"])

    if st.session_state.is_mobile:
        uploaded_audio = st.file_uploader("📤 Upload an audio file (WAV/MP3)", type=["wav", "mp3"])
        if uploaded_audio:
            audio_dict = {"bytes": uploaded_audio.read()}
    else:
        audio_dict = mic_recorder(start_prompt="🎤 Speak Topic" if lang == "en" else "🎤 Thema sprechen")

    if audio_dict:
        topic = transcribe_audio(audio_dict)
        if topic:
            st.success(f"✅ You said: {topic}")
            st.session_state.story = f"Generating a story about {topic}..."
            st.rerun()

# 🌟 Generate Initial Story
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

# 📖 Play and Display Story
if st.session_state.story and st.session_state.audio_file:
    st.markdown(f"<p style='font-size:18px;'>{st.session_state.story}</p>", unsafe_allow_html=True)
    st.audio(st.session_state.audio_file, format="audio/mp3")
