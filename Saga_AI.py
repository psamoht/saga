import streamlit as st
import openai
import locale
import re
import time

# OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🌍 Detect system language for default selection
user_locale = locale.getdefaultlocale()[0]
default_lang = "de" if user_locale and "de" in user_locale else "en"

# 🌐 Language Selection Dropdown
lang_options = {"English": "en", "Deutsch": "de"}
selected_lang = st.selectbox("🌍 Select Language / Sprache wählen:", list(lang_options.keys()), index=0 if default_lang == "en" else 1)
lang = lang_options[selected_lang]

# 🏗 Session State for story progression
if "story" not in st.session_state:
    st.session_state.story = ""
if "options" not in st.session_state:
    st.session_state.options = []
if "history" not in st.session_state:
    st.session_state.history = []

# 📜 Start of Streamlit UI
st.title("📖 Saga – Be Part of the Story" if lang == "en" else "📖 Saga – Sei Teil der Geschichte")
topic = st.text_input("🌟 Choose a topic for your story:" if lang == "en" else "🌟 Wähle ein Thema für deine Geschichte:")

# 🎩 Add loading GIF
loading_gif = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzc1NmJjN2JkN2Q0N2E5OGY3YmI5NzJiZjI1Y2Q1NDRjMWYwMmJhZiZjdD1n/26BRzozg4TCBXv6QU/giphy.gif"

def generate_story(user_topic, user_choice=None):
    """Handles story generation with OpenAI API."""
    with st.spinner("🪄 The story magic is happening..."):
        time.sleep(1)  # Small delay for smooth UX
        with st.empty():
            st.image(loading_gif, use_column_width=True)

        try:
            prompt = f"Write a children's story about {user_topic}. "
            if user_choice:
                prompt += f"The reader chose: {user_choice}. Continue the story."

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Create a fun, engaging children's story for a 5-year-old in {lang}. "
                                                  f"Each section should be around 200 words long. "
                                                  f"The story should flow naturally and end at a logical decision point, "
                                                  f"where two possible story paths emerge. "
                                                  f"The decisions should feel like a natural part of the story, without directly addressing the reader. "
                                                  f"Clearly separate the two options at the end, with each option on a separate line."},
                    {"role": "user", "content": prompt}
                ]
            )

            full_story_response = response.choices[0].message.content

            # 🏷 Extract the main story and the two decision options
            story_lines = full_story_response.strip().split("\n")
            story_text = "\n\n".join(story_lines[:-2]).strip()
            options = [story_lines[-2].strip(), story_lines[-1].strip()]

            return story_text, options

        except Exception as e:
            return f"❌ Error: {str(e)}", []

if topic and not st.session_state.story:
    story_text, options = generate_story(topic)
    st.session_state.history.append(story_text)
    st.session_state.story = story_text
    st.session_state.options = options

# 📖 Display the current story
if st.session_state.story:
    st.markdown(f"<p style='font-size:18px;'>{st.session_state.story}</p>", unsafe_allow_html=True)

    # 🎭 Show decision buttons (Fix for incorrect button text)
    selected_option = None
    if len(st.session_state.options) == 2:
        col1, col2 = st.columns(2)
        with col1:
            if st.button(st.session_state.options[0]):
                selected_option = st.session_state.options[0]
        with col2:
            if st.button(st.session_state.options[1]):
                selected_option = st.session_state.options[1]

    # ⏭️ Continue the story after a decision
    if selected_option:
        story_text, options = generate_story(topic, selected_option)
        st.session_state.history.append(story_text)
        st.session_state.story = story_text
        st.session_state.options = options
        st.rerun()
