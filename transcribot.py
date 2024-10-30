import streamlit as st
import yt_dlp
import assemblyai as aai
import os
from fpdf import FPDF
from dotenv import load_dotenv
import requests
from PyPDF2 import PdfReader
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.colored_header import colored_header

# Load environment variables from .env file
load_dotenv()

# AssemblyAI and OpenAI API keys
aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')
openai_api_key = os.getenv("OPENAI_API_KEY")

# Utility to download YouTube audio and retrieve video title and stats
def download_audio(youtube_url):
    audio_file_path = "audio"
    video_info = None

    if os.path.exists(audio_file_path + ".mp3"):
        os.remove(audio_file_path + ".mp3")
        print("Existing audio file deleted.")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': audio_file_path,
            'restrictfilenames': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(youtube_url, download=True)
            print("Download completed successfully!")

    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None, None

    return audio_file_path + ".mp3", video_info

# Utility to transcribe audio using AssemblyAI
def transcribe_audio(audio_file):
    if not os.path.exists(audio_file):
        print(f"Error: Audio file '{audio_file}' not found.")
        return None

    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(speaker_labels=True)

    try:
        transcript = transcriber.transcribe(audio_file, config)
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

    if transcript.status == aai.TranscriptStatus.error:
        print(f"Transcription failed: {transcript.error}")
        return None

    return transcript

# Utility to save transcription to PDF, including video title
def save_transcription_to_pdf(text, utterances, file_path, title=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", style='B', size=14)

    # Add the video title as a heading
    if title:
        pdf.cell(0, 10, title, ln=True, align="C")
        pdf.ln(10)

    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)

    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, "Speaker Labels:", ln=True)
    pdf.set_font("Arial", size=12)

    for utterance in utterances:
        pdf.multi_cell(0, 10, f"Speaker {utterance.speaker}: {utterance.text}")

    pdf.output(file_path)
    print(f"Transcription saved as {file_path}.")

# Utility to interact with OpenAI API
def ask_question(question, context):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": context},
            {"role": "user", "content": question},
        ],
        "temperature": 0.7,
        "max_tokens": 256,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# Function to extract text from a PDF using PyPDF2
def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

# Function to preview PDF content (first few pages)
def preview_pdf(file_path, preview_length=2):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages[:preview_length]:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return "Failed to preview PDF content."

# Main Streamlit Application
def main():
    st.markdown("<h1 style='font-family:Arial;'>Transcribot</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-family:Arial; font-size:1.1em;'>AI Driven YouTube Transcription and Interactive Q/A Bot</p>", unsafe_allow_html=True)

    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Organize the app with tabs
    tab1, tab2 = st.tabs(["Transcription & Q&A", "Chat History"])

    with tab1:
        # Visual Step Progression
        st.markdown("<h2 style='font-family:Arial;'>Step 1: Enter YouTube URL</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-family:Arial; font-size:1em;'>Provide a video URL to download and transcribe audio.</p>", unsafe_allow_html=True)

        youtube_url = st.text_input("YouTube Video Link:")

        if st.button("Start Transcription"):
            with st.spinner("Retrieving audio..."):
                audio_file_path, video_info = download_audio(youtube_url)

            if audio_file_path and video_info:
                st.success(f"Downloaded Audio: {video_info['title']}")
                
                # Display optional video statistics
                st.markdown("<h3 style='font-family:Arial;'>Video Stats</h3>", unsafe_allow_html=True)
                st.write(f"**Channel Name:** {video_info.get('uploader')}")
                st.write(f"**Views:** {video_info.get('view_count')}")
                st.write(f"**Title:** {video_info.get('title')}")

                # Play the audio directly on the app
                st.audio(audio_file_path, format='audio/mp3')

                # Transcription Status Indicator
                with st.spinner("Transcribing audio..."):
                    transcript = transcribe_audio(audio_file_path)

                if transcript:
                    st.success("Audio transcribed successfully!")
                    st.write(f"Preview: {transcript.text[:200]}...")

                    pdf_filename = "transcription.pdf"
                    save_transcription_to_pdf(transcript.text, transcript.utterances, pdf_filename, video_info['title'])

                    # Provide options to download audio and transcription PDF only after successful transcription
                    with open(audio_file_path, "rb") as audio_file:
                        st.download_button(
                            label="Download Audio",
                            data=audio_file.read(),
                            file_name="downloaded_audio.mp3",
                            mime="audio/mpeg"
                        )

                    with open(pdf_filename, "rb") as pdf_file:
                        st.download_button(
                            label="Download Transcription PDF",
                            data=pdf_file.read(),
                            file_name=pdf_filename,
                            mime="application/pdf"
                        )

                    # PDF Preview Feature
                    st.markdown("<h3 style='font-family:Arial;'>Preview Transcription PDF</h3>", unsafe_allow_html=True)
                    preview_text = preview_pdf(pdf_filename)
                    st.text_area("PDF Preview", preview_text, height=250)
                    
            else:
                st.error("Failed to download audio. Please check the YouTube link and try again.")

        add_vertical_space(2)

        st.markdown("<h2 style='font-family:Arial;'>Step 2: Chat Based on Transcription</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-family:Arial; font-size:1em;'>Interactively ask questions to learn from the transcribed content.</p>", unsafe_allow_html=True)
        
        question = st.text_input("Ask a question about the transcribed content")

        if question:
            if os.path.exists("transcription.pdf"):
                context = extract_text_from_pdf("transcription.pdf")
                answer = ask_question(question, context)
                st.session_state.chat_history.append((question, answer))
                st.write("Answer:", answer)
            else:
                st.error("Please transcribe a video first.")

    with tab2:
        st.markdown("<h3 style='font-family:Arial;'>Chat History</h3>", unsafe_allow_html=True)
        if st.session_state.chat_history:
            for i, (q, a) in enumerate(st.session_state.chat_history):
                st.markdown(f"**Q{i+1}:** {q}")
                st.markdown(f"**A{i+1}:** {a}")
                st.divider()
        else:
            st.info("No chat history available.")

if __name__ == "__main__":
    main()
