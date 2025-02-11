import streamlit as st
import openai

# OpenAI API-Schlüssel aus den Streamlit Secrets laden
openai.api_key = st.secrets["OPENAI_API_KEY"]

# App-Titel
st.title("📖 Saga – Erlebe deine eigene interaktive Geschichte")
st.subheader("🌟 Wähle ein Thema für deine Geschichte:")

# Session State für Story und Entscheidungsoptionen
if "story" not in st.session_state:
    st.session_state.story = ""
if "options" not in st.session_state:
    st.session_state.options = []
if "history" not in st.session_state:
    st.session_state.history = []  # Speichert die Geschichte für den Kontext

# Nutzer gibt ein Thema für die Geschichte ein
topic = st.text_input("Beispiel: Eine Geschichte über einen Bagger")

if topic and not st.session_state.story:
    try:
        # GPT-4o Mini generiert den ersten Abschnitt mit einer offenen Handlung
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": 
                    "Erzähle eine interaktive Kindergeschichte, die immer an einem logischen Entscheidungspunkt endet. "
                    "Beschreibe eine Szene, entwickle die Handlung, aber lasse die Geschichte mit genau zwei möglichen "
                    "Entscheidungen offen. Formuliere keine Lösung oder einen Abschluss."
                },
                {"role": "user", "content": f"Erstelle eine Kindergeschichte über {topic} "
                                            "und gib am Ende genau zwei Entscheidungsoptionen."}
            ]
        )

        story_response = response.choices[0].message.content

        # Die Geschichte in den Session State übernehmen
        st.session_state.history.append(story_response)
        st.session_state.story = story_response

        # Zwei Entscheidungsoptionen extrahieren
        next_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Basierend auf dieser Geschichte, generiere exakt zwei sinnvolle Entscheidungsoptionen "
                                              "für den Nutzer. Gib nur die zwei Optionen aus, ohne zusätzliche Story."},
                {"role": "user", "content": f"Die Geschichte endet an folgendem Entscheidungspunkt:\n\n{story_response}\n\n"
                                            "Welche zwei Optionen hat die Hauptfigur jetzt?"}
            ]
        )

        st.session_state.options = next_response.choices[0].message.content.split("\n")

    except Exception as e:
        st.error(f"❌ Fehler: {str(e)}")

# Zeige die aktuelle Geschichte an
if st.session_state.story:
    st.write(st.session_state.story)

    # Falls Entscheidungsoptionen vorhanden sind, zeige sie als Buttons
    selected_option = None
    if len(st.session_state.options) == 2:
        if st.button(st.session_state.options[0]):
            selected_option = st.session_state.options[0]
        if st.button(st.session_state.options[1]):
            selected_option = st.session_state.options[1]

    # Falls der Nutzer eine Entscheidung getroffen hat, geht die Geschichte weiter
    if selected_option:
        try:
            next_story_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Erzähle die Geschichte weiter, basierend auf der Entscheidung des Nutzers. "
                                                  "Die Geschichte endet wieder an einem neuen logischen Entscheidungspunkt."},
                    {"role": "user", "content": f"Die bisherige Geschichte:\n\n{'\n\n'.join(st.session_state.history)}\n\n"
                                                f"Der Nutzer hat sich entschieden für: {selected_option}\n\n"
                                                "Setze die Geschichte fort und gib am Ende genau zwei neue Entscheidungsoptionen."}
                ]
            )

            new_story_part = next_story_response.choices[0].message.content
            st.session_state.history.append(new_story_part)
            st.session_state.story = new_story_part

            # Neue Entscheidungsoptionen abrufen
            next_options_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Generiere exakt zwei neue Entscheidungsoptionen, die logisch aus der Geschichte folgen."},
                    {"role": "user", "content": f"Die Geschichte endet an folgendem Punkt:\n\n{new_story_part}\n\n"
                                                "Welche zwei sinnvollen Optionen gibt es jetzt für die Hauptfigur?"}
                ]
            )

            st.session_state.options = next_options_response.choices[0].message.content.split("\n")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Fehler: {str(e)}")
