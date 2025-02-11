import streamlit as st
import openai

# OpenAI API-Schlüssel aus den Streamlit Secrets laden
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Streamlit UI
st.title("📖 AI Box - Interaktive Geschichten für Kinder")
st.subheader("🌟 Gib ein Thema für deine Geschichte ein:")

# Session State für Geschichte und Optionen
if "story" not in st.session_state:
    st.session_state.story = ""
if "options" not in st.session_state:
    st.session_state.options = []

# Eingabe durch den Nutzer
topic = st.text_input("Beispiel: Eine Geschichte über einen Bagger")

if topic and not st.session_state.story:
    try:
        # GPT-4o Mini generiert die erste Story mit zwei Optionen
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Erzähle eine interaktive Kindergeschichte. "
                                              "Beende die Geschichte nicht und erzeuge immer genau zwei Entscheidungsoptionen."},
                {"role": "user", "content": f"Erstelle eine Kindergeschichte über {topic} "
                                            "und gib mir am Ende genau zwei Entscheidungsoptionen."}
            ]
        )

        story_response = response.choices[0].message.content
        # Die Geschichte und die Entscheidungsoptionen aufteilen
        story_parts = story_response.split("\n\n")
        story_text = story_parts[0]  # Die Geschichte
        options = story_parts[1:] if len(story_parts) > 1 else ["Weiter", "Etwas anderes tun"]

        # Speichern der Werte
        st.session_state.story = story_text
        st.session_state.options = options

    except Exception as e:
        st.error(f"❌ Fehler: {str(e)}")

# Zeige die aktuelle Geschichte an
if st.session_state.story:
    st.write(st.session_state.story)

    # Zeige die Entscheidungsoptionen als Buttons an
    selected_option = None
    for option in st.session_state.options:
        if st.button(option):
            selected_option = option

    # Falls eine Option gewählt wurde, geht die Geschichte weiter
    if selected_option:
        try:
            next_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Erzähle die Kindergeschichte weiter, basierend auf der folgenden Entscheidung. "
                                                  "Erfinde keine neuen Optionen, sondern setze die Geschichte basierend auf der Wahl fort. "
                                                  "Gib am Ende genau zwei neue Entscheidungsoptionen."},
                    {"role": "user", "content": f"Die bisherige Geschichte: {st.session_state.story} "
                                                f"Die getroffene Entscheidung: {selected_option} "
                                                "Setze die Geschichte fort und gib am Ende zwei neue Optionen."}
                ]
            )

            next_story_response = next_response.choices[0].message.content
            story_parts = next_story_response.split("\n\n")
            next_story_text = story_parts[0]
            new_options = story_parts[1:] if len(story_parts) > 1 else ["Weiter", "Etwas anderes tun"]

            # Speichere die Geschichte weiter
            st.session_state.story += "\n\n" + next_story_text
            st.session_state.options = new_options
            st.experimental_rerun()  # Aktualisiere die UI mit der neuen Story

        except Exception as e:
            st.error(f"❌ Fehler: {str(e)}")
