import asyncio
import vlc
import random
import time
from mutagen.mp3 import MP3
import edge_tts
from edge_tts import VoicesManager
from deep_translator import GoogleTranslator
# from googletrans import Translator
from indic_transliteration.sanscript import transliterate, HK, TELUGU
from langdetect import detect_langs

def transliterate_telugu(text):
    result = transliterate(text, HK, TELUGU)
    return result

# def translate_online(text):
#     translator = Translator()
#     translated = translator.translate(text, src="en", dest="te")
#     return translated.text

def translate_offline(text):
   return GoogleTranslator(source="en", target="te").translate(text)

def handle_eng2tel_output(text):
    
    #1. If it is pure telugu, return it
    if any('\u0C00' <= char <= '\u0C7F' for char in text):
        return text
    
    # 2. Use langdetect to get language probabilities
    try:
        langs = detect_langs(text)
    except Exception as e:
        langs = []  

    for lang in langs:
        if lang.lang == "te" and lang.prob > 0.1:
            return transliterate_telugu(text)
    
    return translate_offline(text)
    

def handle_tel2eng_input(text: str) -> str:
    """This function handles Telugu input, translating it to English.

    It supports two Telugu input formats:
    1.  Pure Telugu (e.g., "స్వచ్ఛమైన తెలుగు").
    2.  Romanized Telugu (e.g., "ela unnavu").

    Args:
        text (str): The input text, which can be in Telugu (pure or Romanized) or English.

    Returns:
        str: Returns the input string translated to English. If the input is English, it returns the input string.
        Note: If language detection fails, the function will default to treating the input as English.

    Examples:
        >>> handle_telugu_input("ఎలా ఉన్నారు?")
        'How are you?'

        >>> handle_telugu_input("ela unnaru?")
        'How are you?'

        >>> handle_telugu_input("Hello")
        'Hello'

    Author:
        Krishna Bhagavan K.
        Aditya University
    """
    
    # Checking for Pure telugu
    if any('\u0C00' <= char <= '\u0C7F' for char in text):
        return GoogleTranslator(source="te", target="en").translate(text)
    
    # Checking probability of a language
    try:
        langs = detect_langs(text)
    except Exception as e:
        langs = [] 

    # Checking for literate telugu(english written telugu)
    for lang in langs:
        if lang.lang == "te" and lang.prob > 0.1:
            return GoogleTranslator(source="te", target="en").translate(transliterate_telugu(text))
        
    # Returns english text
    return text

#Function to speak telugu
async def amain(text,audio_file) -> None:
    voices = await VoicesManager.create()
    voice = voices.find(Gender="Male", Language="te")
    communicate = edge_tts.Communicate(text, random.choice(voice)["Name"])
    await communicate.save(audio_file)
    audio = MP3(audio_file)
    duration = audio.info.length
    player = vlc.MediaPlayer(audio_file)
    player.play()
    time.sleep(duration+1)
    player.stop()

# if __name__ == "__main__":
    # audio_file = "telugu.mp3"
    # text = "I'm really glad to know that you are alive"
    # pure_telugu = process_text(text)
    # asyncio.run(amain(pure_telugu,audio_file))
