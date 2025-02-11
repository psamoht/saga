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

# 🏗 Session State for story and choices
if "story" not in st.session_state:
    st.session_state.story = ""
if "options" not in st.session_state:
    st.session_state.options = []
if "history" not in st.session_state:
    st.session_state.history = []

# 📝 Extract main character's name dynamically
def extract_main_character(story_text):
    match = re.search(r"\b([A-ZÄÖÜ][a-zäöü]+)\b", story_text)
    return match.group(1) if match else "the character"

# 📜 Start of Streamlit UI
st.title("📖 Saga – Be Part of the Story" if lang == "en" else "📖 Saga – Sei Teil der Geschichte")
topic = st.text_input("🌟 Choose a topic for your story:" if lang == "en" else "🌟 Wähle ein Thema für deine Geschichte:")

if topic and not st.session_state.story:
    try:
        # 🎭 Generate initial story with ~200 words and a natural decision transition
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Create a fun and engaging children's story for a 5-year-old in {lang}. "
                                              f"Each section should be about 200 words long and end at a logical decision point. "
                                              f"Do NOT include decision options in the text. "
                                              f"Use simple, playful language for kids."},
                {"role": "user", "content": f"Write a children's story about {topic}. "
                                            f"The story should end in a way that naturally leads to a choice the reader must make."}
            ]
        )

        story_response = response.choices[0].message.content
        st.session_state.history.append(story_response)
        st.session_state.story = story_response

        # 🏷 Extract main character's name
        main_character = extract_main_character(story_response)

        # 🎭 Generate a natural decision transition
        decision_prompt_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Create a smooth, natural transition for a children's story in {lang}, "
                                              f"leading the reader to make a decision. "
                                              f"Use playful and easy-to-understand language suitable for a 5-year-old."},
                {"role": "user", "content": f"The story ends here:\n\n{story_response}\n\n"
                                            f"Write a natural transition leading to a choice for {main_character}."}
            ]
        )

        st.session_state.decision_prompt = decision_prompt_response.choices[0].message.content

        # 🎭 Generate two natural decision options
        next_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Generate exactly two simple, natural choices for a 5-year-old in {lang}. "
                                              f"The choices should sound playful and easy to understand. "
                                              f"Use short sentences. Do NOT write a question, only the two choices."},
                {"role": "user", "content": f"The story ends here:\n\n{story_response}\n\n"
                                            f"What are two natural choices for {main_character}?"}
            ]
        )

        st.session_state.options = next_response.choices[0].message.content.split("\n")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# 📖 Display the current story
if st.session_state.story:
    st.markdown(f"<p style='font-size:18px;'>{st.session_state.story}</p>", unsafe_allow_html=True)

    # 🛤️ Show smooth transition to decision point (same size as story text)
    if hasattr(st.session_state, "decision_prompt"):
        st.markdown(f"<p style='font-size:18px;'><b>{st.session_state.decision_prompt}</b></p>", unsafe_allow_html=True)

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
                    {"role": "system", "content": f"Continue the story based on the selected choice in {lang}. "
                                                  f"Each section should be about 200 words long "
                                                  f"and end with a smooth transition to a new decision point. "
                                                  f"Do NOT include decision options in the text."},
                    {"role": "user", "content": f"The story so far:\n\n{'\n\n'.join(st.session_state.history)}\n\n"
                                                f"The reader chose: {selected_option}\n\n"
                                                f"Continue the story naturally."}
                ]
            )

            new_story_part = next_story_response.choices[0].message.content
            st.session_state.history.append(new_story_part)
            st.session_state.story = new_story_part

            # 🏷 Extract main character's name again
            main_character = extract_main_character(new_story_part)

            # 🎭 Generate a new natural transition to the next decision
            decision_prompt_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Create a smooth, playful transition in {lang}, leading the reader to the next decision. "
                                                  f"It should feel like a natural part of the story."},
                    {"role": "user", "content": f"The story now ends here:\n\n{new_story_part}\n\n"
                                                f"Write a natural transition leading the reader to make a choice for {main_character}."}
                ]
            )

            st.session_state.decision_prompt = decision_prompt_response.choices[0].message.content

            # 🔁 Generate two new decision options
            next_options_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Generate exactly two new, playful choices in {lang}, "
                                                  f"that are simple and engaging for a 5-year-old. "
                                                  f"Use short and easy-to-understand words."},
                    {"role": "user", "content": f"The story ends here:\n\n{new_story_part}\n\n"
                                                f"What are two fun and natural choices for {main_character}?"}
                ]
            )

            st.session_state.options = next_options_response.choices[0].message.content.split("\n")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
