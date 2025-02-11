import streamlit as st
import openai
import locale
import re

# OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🌍 Detect system language
user_locale = locale.getdefaultlocale()[0]
if user_locale and "de" in user_locale:
    lang = "de"
    title = "📖 Saga – Sei Teil der Geschichte"
    input_label = "🌟 Wähle ein Thema für deine Geschichte:"
else:
    lang = "en"
    title = "📖 Saga – Be Part of the Story"
    input_label = "🌟 Choose a topic for your story:"

# 🏗 Session State for story and choices
if "story" not in st.session_state:
    st.session_state.story = ""
if "options" not in st.session_state:
    st.session_state.options = []
if "history" not in st.session_state:
    st.session_state.history = []

# 📝 Extract main character's name dynamically
def extract_main_character(story_text):
    match = re.search(r"\b([A-Z][a-z]+)\b", story_text)
    return match.group(1) if match else "the character"

# 📜 Start of Streamlit UI
st.title(title)
topic = st.text_input(input_label)

if topic and not st.session_state.story:
    try:
        # 🎭 Generate initial story with a personalized decision prompt
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Create an interactive children's story for 5-year-olds in {lang}. "
                                              f"Each section should be about 300 words long and end at a logical decision point. "
                                              f"Do NOT include the decision options in the story text."},
                {"role": "user", "content": f"Write a children's story about {topic}. "
                                            f"The story should end with a clear decision point for the character."}
            ]
        )

        story_response = response.choices[0].message.content
        st.session_state.history.append(story_response)
        st.session_state.story = story_response

        # 🏷 Extract main character's name
        main_character = extract_main_character(story_response)

        # 🎭 Generate personalized decision prompt
        decision_prompt_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Generate a short, natural-sounding decision question for a children's story "
                                              f"in {lang}, using the name '{main_character}'. "
                                              f"It should feel like part of the story."},
                {"role": "user", "content": f"The story ends here:\n\n{story_response}\n\n"
                                            f"What is a natural decision prompt to ask the reader about what {main_character} should do next?"}
            ]
        )

        st.session_state.decision_prompt = decision_prompt_response.choices[0].message.content

        # 🎭 Generate two decision options
        next_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Generate exactly two logical decision options in {lang} "
                                              f"that follow from the story. "
                                              f"Write ONLY the two choices, NOT the question or any extra text."},
                {"role": "user", "content": f"The story ends at this decision point:\n\n{story_response}\n\n"
                                            f"What are two logical choices for {main_character}?"}
            ]
        )

        st.session_state.options = next_response.choices[0].message.content.split("\n")

    except Exception as e:
        st.error(f"❌ Fehler: {str(e)}")

# 📖 Display the current story
if st.session_state.story:
    st.write(st.session_state.story)

    # 🛤️ Show dynamic, personalized decision prompt
    if hasattr(st.session_state, "decision_prompt"):
        st.subheader(st.session_state.decision_prompt)

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
                                                  f"Each section should be about 300 words long and end with a logical decision point. "
                                                  f"Do NOT include decision options in the text."},
                    {"role": "user", "content": f"The story so far:\n\n{'\n\n'.join(st.session_state.history)}\n\n"
                                                f"The reader chose: {selected_option}\n\n"
                                                f"Continue the story."}
                ]
            )

            new_story_part = next_story_response.choices[0].message.content
            st.session_state.history.append(new_story_part)
            st.session_state.story = new_story_part

            # 🏷 Extract main character's name again (in case of new characters)
            main_character = extract_main_character(new_story_part)

            # 🎭 Generate a new personalized decision prompt
            decision_prompt_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Generate a short, natural-sounding decision question for a children's story "
                                                  f"in {lang}, using the name '{main_character}'. "
                                                  f"It should feel like part of the story."},
                    {"role": "user", "content": f"The story now ends here:\n\n{new_story_part}\n\n"
                                                f"What is a natural decision prompt to ask the reader about what {main_character} should do next?"}
                ]
            )

            st.session_state.decision_prompt = decision_prompt_response.choices[0].message.content

            # 🔁 Generate two new decision options
            next_options_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Generate exactly two new decision options in {lang} "
                                                  f"that logically follow from the story. "
                                                  f"Write ONLY the two choices, NOT the question or any extra text."},
                    {"role": "user", "content": f"The story ends at this point:\n\n{new_story_part}\n\n"
                                                f"What are two logical choices for {main_character}?"}
                ]
            )

            st.session_state.options = next_options_response.choices[0].message.content.split("\n")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Fehler: {str(e)}")
