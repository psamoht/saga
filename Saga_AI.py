import streamlit as st
import openai
import locale
import re

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

if topic and not st.session_state.story:
    try:
        # 📝 Generate first section with a decision point
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Create a fun, engaging children's story for a 5-year-old in {lang}. "
                                              f"Each section should be around 200 words long. "
                                              f"The story should flow naturally and end at a logical decision point, "
                                              f"where two possible story paths emerge. "
                                              f"The decisions should feel like a natural part of the story, without directly addressing the reader. "
                                              f"Clearly separate the two options at the end."},
                {"role": "user", "content": f"Write a children's story about {topic}. "
                                            f"Make sure that each story section is about 200 words long, "
                                            f"ending with two choices for the next part of the story."}
            ]
        )

        full_story_response = response.choices[0].message.content

        # 🏷 Extract the main story and the two decision options
        story_parts = full_story_response.split("\n\n")
        story_text = "\n\n".join(story_parts[:-2])  # The actual story
        options = story_parts[-2:]  # Last two lines contain the choices

        st.session_state.history.append(story_text)
        st.session_state.story = story_text
        st.session_state.options = [opt.strip() for opt in options if opt.strip()]

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# 📖 Display the current story
if st.session_state.story:
    st.markdown(f"<p style='font-size:18px;'>{st.session_state.story}</p>", unsafe_allow_html=True)

    # 🎭 Show decision buttons
    selected_option = None
    if len(st.session_state.options) == 2:
        if st.button(st.session_state.options[0]):
            selected_option = st.session_state.options[0]
        if st.button(st.session_state.options[1]):
            selected_option = st.session_state.options[1]

    # ⏭️ Continue the story after a decision
    if selected_option:
        try:
            next_story_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Continue the children's story in {lang}, maintaining a fun, engaging tone. "
                                                  f"Each section should be around 200 words long and end with a logical decision point. "
                                                  f"The decisions should feel like a natural part of the story, "
                                                  f"without directly addressing the reader. "
                                                  f"Clearly separate the two options at the end."},
                    {"role": "user", "content": f"The story so far:\n\n{'\n\n'.join(st.session_state.history)}\n\n"
                                                f"The reader chose: {selected_option}\n\n"
                                                f"Continue the story, keeping it immersive and ending with two choices for the next step."}
                ]
            )

            new_full_story_response = next_story_response.choices[0].message.content

            # 🏷 Extract the new main story and the next two decision options
            story_parts = new_full_story_response.split("\n\n")
            new_story_text = "\n\n".join(story_parts[:-2])  # The actual story
            new_options = story_parts[-2:]  # Last two lines contain the choices

            st.session_state.history.append(new_story_text)
            st.session_state.story = new_story_text
            st.session_state.options = [opt.strip() for opt in new_options if opt.strip()]
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
