import streamlit as st
import openai

# OpenAI API Key aus den Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Streamlit UI
st.title("📖 AI Box - Interaktive Geschichten für Kinder")
st.subheader("🌟 Gib ein Thema für deine Geschichte ein:")

# Eingabe durch den Nutzer
topic = st.text_input("Beispiel: Ein Abenteuer mit einem Drachen")

if topic:
    try:
        # GPT-4 Turbo API Anfrage mit neuer Syntax
        response = openai.chat.completions.create(
            model="gpt-4-turbo-2024-02-06",
            messages=[
                {"role": "system", "content": "Erzähle eine interaktive Kindergeschichte"},
                {"role": "user", "content": f"Erstelle eine Kindergeschichte über {topic}."}
            ]
        )
        
        story = response.choices[0].message.content
        st.write(story)

        # Entscheidungsoptionen für den Nutzer
        st.subheader("🛤️ Wie soll die Geschichte weitergehen?")
        option1 = st.button("🚪 Gehe in die Höhle")
        option2 = st.button("🌲 Laufe durch den Wald")

        if option1:
            next_response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "Erzähle eine interaktive Kindergeschichte"},
                    {"role": "user", "content": f"Die Hauptfigur geht in die Höhle. Wie geht es weiter?"}
                ]
            )
            st.write(next_response.choices[0].message.content)
        
        if option2:
            next_response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "Erzähle eine interaktive Kindergeschichte"},
                    {"role": "user", "content": f"Die Hauptfigur läuft durch den Wald. Wie geht es weiter?"}
                ]
            )
            st.write(next_response.choices[0].message.content)

    except Exception as e:
        st.error(f"❌ Fehler: {str(e)}")
