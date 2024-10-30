# Transcribot

Transcribot is an AI-driven YouTube transcription and interactive Q&A bot built with Streamlit. This application allows users to input a YouTube video link, download and transcribe the audio, and then interactively ask questions based on the transcription. The transcribed content can also be downloaded as a PDF file.

## Features

- **YouTube Audio Download**: Input a YouTube link to download the audio file in MP3 format.
- **Automatic Transcription**: Transcribe the downloaded audio using AssemblyAI's transcription service.
- **Interactive Q&A**: Ask questions about the transcribed content using OpenAI's GPT-3.5 API.
- **PDF Export**: Save the transcription with speaker labels as a downloadable PDF.
- **Chat History**: View previous questions and answers related to the transcription.

## Install Dependencies 

        pip install -r requirements.txt

## Set up API keys:

    Create a .env file in the root directory.
    Add your AssemblyAI and OpenAI API keys:
        ASSEMBLYAI_API_KEY=your_assemblyai_api_key
        OPENAI_API_KEY=your_openai_api_key

## Instructions
    Enter YouTube URL: Copy and paste a YouTube video link and click "Start Transcription."
    View Transcription & Download: Once transcribed, preview and download the transcription as a PDF.
    Interactive Q&A: Ask questions based on the transcribed text.
    Chat History: Review past Q&A interactions within the session.
