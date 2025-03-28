import os
import getpass
import curses
from telugu_translator import handle_eng2tel_output, handle_tel2eng_input
from lang_selector_cli import choose_language
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START,MessagesState, END
from langgraph.checkpoint.memory import MemorySaver
import google.generativeai as genai
import speech_recognition as sr
from dotenv import load_dotenv
from PIL import Image, ImageGrab
import pyperclip
import cv2
import asyncio
from tts import speak

load_dotenv()

# Load and intialiaze the agent
def initialize_models():
    
    if not os.environ.get("GROQ_API_KEY"):
        os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your GROQ_API_KEY: ")
    model = init_chat_model("llama3-70b-8192",model_provider="groq").bind_tools(tools)

    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    generation_config = {
        'temperature': 0.7,
        'top_p': 1,
        'top_k': 1,
        'max_output_tokens': 2048
    }
    # safety_settings = [
    #     {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_NONE'},
    #     {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_NONE'},
    #     {'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'threshold': 'BLOCK_NONE'},
    #     {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_NONE'}
    # ]
    genai_model = genai.GenerativeModel('gemini-1.5-flash-latest',
                                        generation_config=generation_config,
                                        safety_settings=None)
    return [model,genai_model]


# Load the tools
def define_tools():
    
    @tool
    def get_copied_text():
        """Return the clipboard content using pyperclip library paste() function"""
        clipboard_content = pyperclip.paste()
        return clipboard_content if isinstance(clipboard_content, str) else None
    
    @tool
    def webcam_capture():
        """Capture the image from the webcam and return its file path to describe_image tool for visual context"""
        webcam = cv2.VideoCapture(0)
        path = "webcam.jpg"
        if not webcam.isOpened():
            raise Exception("Error: WebCam did not opened")
        ret, frame = webcam.read()
        if ret:
            cv2.imwrite(path,frame)
            return path
        else:
            raise Exception("Failed to capture webcam image")
        
    @tool
    def describe_image(image_path: str):
        """Takes the image_path as argument and returns the visual context"""
        img = Image.open(image_path)
        prompt = (
            'You are the vision analysis AI that provides semantic meaning from images to provide context '
            'to send to another AI that will create a response to the user. Do not respond as the AI assistant '
            'to the user. Instead take the user prompt input and try to extract all meaning from the photo '
            'relevant to the user prompt. Then generate as much objective data about the image for the AI '
        )
        
        response = models[1].generate_content([prompt, img])
        return response.text

    @tool
    def take_screenshot():
        """It takes the screenshot of user's working device screen and return the image path to describe_image tool"""
        path = 'screenshot.jpg'
        screenshot = ImageGrab.grab()
        screenshot.convert('RGB').save(path, quality=15)
        return path
    
    
        
    tools = [get_copied_text, webcam_capture, take_screenshot, describe_image]
    return tools

def activate_voice(lang: str):
        """when user say activate voice this tool will be called and it returns the transcription of user voice"""
        recognizer = sr.Recognizer()
        with sr.Microphone() as mic:
            print("You can now start speaking.......")
            recognizer.adjust_for_ambient_noise(mic)
            audio = recognizer.listen(mic)
        if lang=="telugu":
            text = recognizer.recognize_google(audio, language="te")
        else:
            text = recognizer.recognize_google(audio, language="en-IN")
        return text


# Define the graph
def graph_builder(tools):
    workflow = StateGraph(MessagesState)
    tool_node = ToolNode(tools)

    def call_model(state: MessagesState):
        predefined_prompts = [
            {"role": "system", "content": "You are a helpful AI assistant. Answer based on user input"},
            {'role': "user", "content": "Hi, I am krishna"},
            {'role': "system", "content": "Nice to meet you, Krishna. I'm glad to know your name"}
        ]
        
        messages = predefined_prompts + state["messages"] #Concatenate the two lists.

        response = models[0].invoke(messages)
        return {"messages": response}
    
    def should_continue(state: MessagesState):
        if not state['messages'][-1].tool_calls:
            return 'end'
        return 'continue'


    workflow.add_node("agent", call_model)
    workflow.add_node("action_tools", tool_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        'agent',
        should_continue,
        {
            "continue": "action_tools",
            "end": END
        },
    )
    workflow.add_edge("action_tools", "agent")

    return workflow


if __name__ == "__main__":
    tools = define_tools()
    models = initialize_models()
    workflow = graph_builder(tools)
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    config = {'configurable': {'thread_id': 't10'}}

    selected_lang = curses.wrapper(choose_language)
    print(f"\n✅ Starting conversation in **{selected_lang.capitalize()}** mode... 🎙️")
    
while True:
    prompt = input("User: ").strip().lower()
    
    if prompt == "exit":
        break

    if prompt == "arise": 
        voice_text = activate_voice(selected_lang)  # Capture voice input
        if voice_text:
            print("User (via voice):", voice_text)
            prompt = voice_text  # Use voice input as prompt
    
    prompt = handle_tel2eng_input(prompt)  # Handle translation if needed
    response = app.invoke({'messages': prompt}, config)['messages'][-1].content  # Get AI response
    
    if selected_lang == 'telugu':
        pure_telugu = handle_eng2tel_output(response)  # Convert response to Telugu
        print('Assistant:', pure_telugu)
        asyncio.run(speak(pure_telugu, "te"))  # Speak response
    else:
        print('Assistant:', response)
        asyncio.run(speak(response, "en"))