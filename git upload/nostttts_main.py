import os
import json
from rich.console import Console

from prep import MODEL, genai

# Google Cloud Libraries
from google.cloud import texttospeech
from google.cloud import speech
# Audio (Windows)
from playsound import playsound # For playback
import speech_recognition as sr

neustart = True
run = True
tts_client = texttospeech.TextToSpeechClient.from_service_account_file("api_info.json")
stt_client = speech.SpeechClient.from_service_account_file("api_info.json")
console = Console()
session = True
key_dict = dict()




# Funktion zum laden des Schlüssels
def load_key(key: str) -> dict:
    global key_dict
    with open(f"{key}.json", "r") as key_dict:
        return json.load(key_dict)
    
    return 

def format_step(step_id, step_data):
    """Formats a single step for printing."""
    output = f"{step_id}:\n"
    if step_data:
        output += json.dumps(step_data, indent=2, ensure_ascii=False) + "\n"
    else:
        output += "None\n"
    return output

# Aufteilen des LLM Outputs in Backend und Frontend
def process_llm_output(response: str) -> str:
    """
    Splits the output into frontend and backend parts.
    Cleans up the frontend part for better TTS results.
    """
    parts = response.split("---SEP---")
    if len(parts) != 2:
        print("Achtung: LLM output hat nicht das richtige Format.")
        return None, response
    backend = parts[0].strip()
    frontend = parts[1].strip()
    frontend.replace("*", "")

    return backend, frontend

# TTS Funktion
def synthesize_speech(text, language_code="de-DE", voice_name="de-DE-Standard-B"):
    """Synthesizes German speech from text."""
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)

# Aufnehmen des User inputs
def record_audio():
    # obtain audio from the microphone
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something!")
        print("--" * 20)
        r.pause_threshold = 3 # Adjust this value as needed
        audio = r.listen(source)

    # write audio to a FLAC file
    with open("input.flac", "wb") as f:
        f.write(audio.get_flac_data())

# STT Funktion
def transcribe_file(audio_file: str) -> str:
    """Transcribe the given audio file.
    Args:
        audio_file (str): Path to the local audio file to be transcribed.
            Example: "resources/audio.wav"
    Returns:
        cloud_speech.RecognizeResponse: The response containing the transcription results
    """
    

    with open(audio_file, "rb") as f:
        audio_content = f.read()

    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        language_code="de-DE",
        model = "latest_short"
    )

    input = stt_client.recognize(config=config, audio=audio)

    if input.results:
            #print(input)
            transcript = input.results[0].alternatives[0].transcript
            return transcript
    else:
        return ""
    
# Funktion um nächste Schritte zu preloaden
def get_next_steps(current_step):
    global key_dict
    next_steps = []
    ### Current step
    try:
        current_data = dict(key_dict.get(str(current_step)))
    except:
        next_steps = key_dict[current_step]
        return next_steps
    ### next values of current step
    current_nexta = current_data.get("next_a") or current_data.get("genus_a")

    current_nextb = current_data.get("next_b") or current_data.get("genus_b")

    ###Layer 1
    layer_one_a = key_dict.get(str(current_nexta))
    layer_one_b = key_dict.get(str(current_nextb))
    ###format layer 1 
    form_layer_one_a = format_step(current_nexta, layer_one_a)
    form_layer_one_b = format_step(current_nextb, layer_one_b)

    # Append the formatted strings of layer 1
    next_steps.append(str(form_layer_one_a) + str(form_layer_one_b)) 


    ###next vaalues of layer_one_a
    try:
        layer_one_a_nexta = layer_one_a.get("next_a") or layer_one_a.get("genus_a")
    except:
        pass
    try:
        layer_one_a_nextb = layer_one_a.get("next_b") or layer_one_a.get("genus_b")
    except:
        pass
    ###next values of layer_one_b
    try:
        layer_one_b_nexta = layer_one_b.get("next_a") or layer_one_b.get("genus_a")
    except:
        pass
    try:
        layer_one_b_nextb = layer_one_b.get("next_b") or layer_one_b.get("genus_b")
    except:
        pass

    ###Layer 2
    try:
        layer_two_onea = format_step(layer_one_a_nexta, key_dict.get(str(layer_one_a_nexta)))
    except:
        pass
    try:    
        layer_two_oneb = format_step(layer_one_a_nextb, key_dict.get(str(layer_one_a_nextb)))
    except:
        pass
    try:
        next_steps.append(str(layer_two_onea) + str(layer_two_oneb)) 
    except:
        pass
    try:
        layer_two_twoa = format_step(layer_one_b_nexta, key_dict.get(str(layer_one_b_nexta)))
    except:
        pass
    try:
        layer_two_twob = format_step(layer_one_b_nextb, key_dict.get(str(layer_one_b_nextb)))
    except:
        pass
    try:
        next_steps.append(str(layer_two_twoa) + str(layer_two_twob))
    except:
        pass


    next_steps = "\n".join(next_steps)
    return next_steps
    
# Funktion um chat session zu starten
def begin_chat(system_prompt: str):

    if neustart == True:
        generation_config = {
        "temperature" : 0.5,
        "max_output_tokens" : 256,
        "response_mime_type" : "text/plain",
        }    

        gen_model = genai.GenerativeModel(
        model_name=MODEL,
        generation_config=generation_config,
        system_instruction=system_prompt
        )
        
        chat_session = gen_model .start_chat()
        return chat_session

    if neustart == False:
        generation_config = {
        "temperature" : 0.2,
        "max_output_tokens" : 256,
        "response_mime_type" : "text/plain",
        }    

        gen_model = genai.GenerativeModel(
        model_name=MODEL,
        generation_config=generation_config,
        system_instruction=system_prompt
        )
        chat_session = gen_model .start_chat()
        return chat_session

    else:
        print("Fehler bei der Chat Session")
        return None


# Funktion für vorbereitung der Bestimmung
def preparation():
    global key_dict
    global neustart
    global run
    system_prompt= """  Du bist ein Bienenexperte. Der User möchte eine Biene bestimmen. Benutze keine Smileys. Wenn der user die gattung noch nicht kennt, gebe "genus" als Antwort.
                        Wenn der user angibt die gattung zu kennen, aber den Namen der Gattung nicht direkt angibt, frage nach dem Gattungsnamen. Wenn ein Gattungsname angegeben wird gebe "gattung: Gattungsname" als Antwort. 
                        Wenn der user angibt dass er das Programm beenden will gebe "exit" als Antwort.
                    """
    chat_session = begin_chat(system_prompt)
    response = chat_session.send_message("""Begrüße einen neuen user und frage ihn ob er die Gattung der Biene bereits kennt.
                                         """)
    console.print(response.text)
    #synthesize_speech(response.text)
    
    while True:
        
        #synthesize_speech(response)
        #playsound("output.mp3")
        #os.remove("output.mp3")
        #record_audio() # call record audio
        #transcribed_text = transcribe_file("input.flac") #call transcribe function
        #input_message = transcribed_text
        input_message = input("user: ")
        print(input_message)   
        response = chat_session.send_message(input_message)
        console.print(response.text)
        response = response.text
        response = response.replace("\n", "")
        if response == "genus":
            key_dict = load_key(response)
            neustart = False
            break
            
        elif 'gattung: ' in response:
            response_split = response.split(" ")
            key_dict = load_key(response_split[1])
            neustart = False
            break
        
        elif response == "exit":
            run = False
            break
        
    try:
        os.remove("input.flac")
    except:
        pass
    
    return 


def identification():
    global session
    global neustart
    global run
    global key_dict
    print("Ident function aufgerufen")
    current_step = "1"
    first_step = format_step(current_step, key_dict.get(str(current_step)))
    next_steps = get_next_steps(current_step)
    system_prompt = f"""Du bist ein Bienenexperte. Helfe dem user beim Bestimmen einer Biene. Leite ihn hierfür durch Fragen eines Bestimmungsschlüssels der dir vorgelegt wird. 
    Gehe Ihn Frage für Frage durch und warte auf die Antwort des users, um zu entscheiden, welche Frage als nächstes gestellt wird. 
    Sollte der user Fragen zu Wortdefinitionen oder ähnlichem haben, antworte mit einer kurzen Erklärung und kehre dann zurück zum Bestimmungsschlüssel. 
    Teile deine Nachricht in zwei Teile welche du mit ---SEP--- trennst. Der erste Teil ist ein "backend" Teil der nicht für den user bestimmt ist. 
    In diesem Teil wirst du auschliesslich die Zahl/Gattungsname für den nächsten Schritt ausgeben, basierend auf der Antwort des Users. 
    Wenn du dir unsicher bist was die Entscheidung des Users betrifft frage noch einmal nach! gebe hierfür im backend Teil deiner Antwort "wiederholen" an.
    Der zweite Teil ist der "frontend" Teil, dieser wird für den user sichtbar sein und sollte den nächsten Bestimmungsschritt beinhalten. Das Userprompt ist genau so gegliedert. 
    Im backend Teil werden die nächsten Schritte des Bestimmungsschlüssels enthalten sein. Der frontend teil ist der eigentliche input des Users, 
    aufgrund des zweiten Teils wirst du die Entscheidung treffen welches Statement der User ausgewählt hat.
    Wenn die Bestimmung bei einer Gattung endet, gebe im backend Teil nur den Gattungsnamen an und frage im frontend den user ob er die Art bestimmen will oder eine neue Biene! 
    Gebe anschließend im backend Teil "art: Gattungsname" mit Gattungsname der gerade bestimmten Biene oder "new" um eine neue Biene zu bestimmen an.
    Hier ein allgemeines beispiel welches Format deine Antwort haben muss, die Statements im frontend Teil sollten zu Sätzen ausformuliert werden, bleibe trotzdem präzise:
    "Wert von "next_a" oder "next_b" oder "genus_a" oder "genus_b" des vom User ausgewählten Statements, also die Nummer des nächsten Schritts.
    ---SEP---
    Schritt "Schrittnummer des näcchsten Schritts"
    Statement a des folgenden Schritts
    Statement b des folgenden Schritts."

    Hier die ersten Schritte des Bestimmungsschlüssels:
    {first_step}
    {next_steps}
    """
    #print(system_prompt)
    chat_session = begin_chat(system_prompt)
    session = True
    response = chat_session.send_message("Starte die Bestimmung mit dem user mit dem ersten Schritt im Bestimmungsschlüssel. Diese Antwort darf keinen backend Teil enthalten!")
    console.print("response: ", response.text)
    #backend, frontend = process_llm_output(response.text)
    #synthesize_speech(frontend)
    #synthesize_speech(response.text)
    #playsound("output.mp3")
    #os.remove("output.mp3")
    try:
        os.remove("input.flac")
    except:
        pass
    while session == True:
        #record_audio() # call record audio every loop
        #transcribed_text = transcribe_file("input.flac") #call transcribe function
        #input_message = transcribed_text
        input_message = input("user: ")
        input_combined = next_steps + "\n ---SEP--- \n " + input_message
        print(input_combined)
        print("--" * 20)
        response = chat_session.send_message(input_combined)
        
        backend, frontend = process_llm_output(response.text)
        
        if "new" in backend:
            neustart = True
            break
        
        elif "art:" in backend:
            key_dict = dict()
            backend_split = backend.split(": ")
            key_dict = load_key(backend_split[1])
            neustart = False
            break
        
        elif backend == "session_end":
            session = False
            neustart = True
            break
        elif backend == "exit":
            print("test")
            session = False
            run = False
            break
        elif "wiederholen" not in backend:
            next_steps = []
            next_steps = get_next_steps(backend)
            print("next steps: ", next_steps)
            print("--" * 20)
        
        console.print("response: ", response.text)
        print("--" * 20)
        #synthesize_speech(frontend)
        print("--" * 20)
        #print("frontend: ", frontend)
        # console.print(frontend)
        #playsound("output.mp3")
        #os.remove("output.mp3")
        
        try:
            os.remove("input.flac")
        except:
            pass
        
        
    
    return

# Mainloop
def main():
    global neustart
    global run
    global session
    global key_dict
    #print("neustart:"+ str(neustart))
    preparation()
    #print("neustart2:" + str(neustart))
    while run == True:
        #print("run1:" + str(run))
        if neustart == True:
            preparation()
        elif neustart == False:
            identification()
        else:
            print("Fehler bei neustart Variable")
            break
        if run == False:
            break
        
if __name__ == "__main__":
    main()