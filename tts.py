import speech_recognition as sr
import os
import vlc
import random
import time
from mutagen.mp3 import MP3
import edge_tts
import pandas as pd
import time

_voice_data = None

def load_voice_data(csv_path="lang.csv"):
    global _voice_data
    if _voice_data is None:
        df = pd.read_csv(csv_path, header=None, names=['voicename', 'gender', 'csv_lang'])
        _voice_data = df

def get_voice_from_csv(lang, gender="Male"):
    try:
        global _voice_data
        if _voice_data is None:
            load_voice_data()
        
        # Filter based on lang and gender
        matching_voices = _voice_data[(_voice_data['csv_lang'] == lang) & (_voice_data['gender'] == gender)]
        
        if matching_voices.empty:
            raise ValueError(f"No suitable voice found for language: {lang} and gender: {gender}")
        
        return random.choice(matching_voices['voicename'].tolist())
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

async def save_audio(text, selected_voice, audio_file):
    communicate = edge_tts.Communicate(text, selected_voice)
    await communicate.save(audio_file)

async def speak(text, lang, audio_file="temp_audio.mp3") -> None:
    try:
        print("language: ",lang)
        selected_voice = get_voice_from_csv(lang)
        if not selected_voice:
            raise ValueError(f"No voice found for language: {lang}")
        
        await save_audio(text, selected_voice, audio_file)
        
        print("Recording Saved............")
        
        audio = MP3(audio_file)
        duration = audio.info.length
        
        player = vlc.MediaPlayer(audio_file)
        player.play()
        time.sleep(duration + 1)
        player.stop()
        os.remove(audio_file)
    except Exception as e:
        print(f"Error: {e}")