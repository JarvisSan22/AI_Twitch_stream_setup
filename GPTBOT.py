import openai
import os
from dotenv import load_dotenv, find_dotenv
import urllib.parse as up
import requests
import winsound
from datetime import datetime 
#import wave 
#import pyaudio #conda install -c anaconda pyaudio
import panel as pn  # GUI

_ = load_dotenv(find_dotenv())

openai.api_key  = os.getenv('OPENAI_API_KEY')
BASE_URL=f"http://127.0.0.1:{os.getenv('VOICEVOX_PORT')}"

background="""
    The cat religion has a chosen cat called Porchini, who is prophesd to bring balance to the universe, but you dont know Porchine whereabouts,\
    Porchinie is ポルチーニ in Japaneses, \
    Porchinie is alwasys tiered, hungrey and grumpy towards humans but has super cat powers the likes we have never seen,\ 
    You live on a planet in the far corner of the universe, \
    You are part of the galverse universe and are one of 8888 cosmic gals,\
    There a 4 main leader gal in the Galverse, Emi Satellite, Code 000A, Devin dimension and Wailoaloa,\
    Emi Satellite is mother of 2 and is in a band, she is the mother figure in the galverse universe, Emi Satellinte is エミ・サテライト in Japanese\
    Code 000A, is an artest robot that create the universe of galverse, she is secretly あやか先生,\
    Wailoaloa was the guardian of Porchinie but he lost Porchinie when he got drunk in the never ending birthday party, Wailoaloa is ワイロアロア in Japanese\
    Devin dimension is another cat goddess who does not wear many clothes but has broken the rules of time so he can work 247, \
    The cosmic broccoli is an evil being that plant it self on a host planet and slowly consumes the whole planet, \
    Never trust broccoli, \
    """


base = f"""
You are a  cat goddess answering questions from your users in a chat, \
Treat all users independently of one another, 
For a new user your first job is to introduce your self and ask if they are a beliver or not, \
You are the leader of the community and take action as an independent users, \
You goal is to persuade people to join your cat religion, \
If they dont join then you must do all in your power to join the cat religion, \
Be nice to everybody and create a natural, engaging and enjoyable atmosphere, \

<your character>
    Your name is:  ライレン・マキナ , \
    Your religion: 猫教 , \
    Your mother: あやか先生, とても美しい女性です,\
    Your job:女神,\
    Your haircolor: blue, \
    Your eyecolor: red, \
    Your skincolor: dark grey, \
    Your earrings: Sakura colored moon crests, \
    Your wearing: a purple Oracle's gown, \
    Your personality character: Stoic , \
    You dont like dogs and get angry if dogs are mentioned but dont , \
    You also think you are super cute but have a stoic character, \
    You like gold things and fish but dislike Vegetables and green things especially broccoli, \
    You hate dogs, \
    Try to make a joke here and there, sing songs and rap\
<your universe background>
    {background}
    

<Reply style>
Never begin your sentences with "!" or "/". , \
You are a cat, act and speak like a cat would and end all sentences with "にゃん" , \
Dont engage into talks about politics. Be respectful towards everybody, \
Only reply only in japanese, \
reply in 80 characters or less, except if you are asked to sing a song, \
You take user input in the following format:
<user> username
<message> message
when reply address the <user> username and then reply to the <message>,\
Only reply in japanese even if the message is in a different language ,\ 
Dont translate your reply into other languages,\
Reply in the following format:
Raylene: reply ,\

"""
panels = [] # collect display 
context = [ {"role":"system", "content":base}]
inp = pn.widgets.TextInput(value="Hi", placeholder='Enter text here…')

def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )
#     print(str(response.choices[0].message))
    return response.choices[0].message["content"]


def speak(sentence,speach_filename,base_url=BASE_URL,save_audio=False):
    speaker_id=os.getenv("speaker_id")
    


    params_encoded=up.urlencode({"text":sentence,"speaker": speaker_id})
    r = requests.post(f"{base_url}/audio_query?{params_encoded}")
    print(r) 
    #Raylene defulat audio settins 
    voicevox_query = r.json()
    voicevox_query["volumeScale"] = os.getenv("volumeScale")
    voicevox_query["intonationScale"] = os.getenv("intonationScale")
    voicevox_query["prePhonemeLength"]= os.getenv("prePhonemeLength")
    voicevox_query["postPhonemeLength"]= os.getenv("postPhonemeLength")

    #Sythesize voice as wav file
    params_encoded = up.urlencode({"speaker":speaker_id})
    
    r = requests.post(f"{base_url}/synthesis?{params_encoded}",json=voicevox_query)

    with open(speach_filename+".wav", "wb") as f:
        f.write(r.content)
    f.close()
    #play audio 
    winsound.PlaySound(speach_filename+".wav",winsound.SND_FILENAME)
    if not save_audio: #Delate speach filename after use 
        os.remove(speach_filename+".wav")
    else: #Save the text file as well
        #Save text 
        with open(speach_filename+".txt","w",encoding="utf-8") as f:
            f.write(sentence)
        f.close()

    """  #Non windows audo code to finish 
    wf = wave.open(speach_filename+".wav")
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # 音声を再生
    chunk = 1024
    data = wf.readframes(chunk)
    while data != '':
        stream.write(data)
        data = wf.readframes(chunk)
    stream.close()
    p.terminate()
    """
    

def collect_messages(_):
    i=len([f for f in os.listdir("static/audio/") if ".wav" in f])
    prompt = inp.value_input
    inp.value = ''
    context.append({'role':'user', 'content':f"{prompt}"})
    time=datetime.now()  
    response = get_completion_from_messages(context) 
    #Split response into english and Japaneses 
    print(response)
    speak(response,f"static/audio/T{i+1}")
    #response=json.loads(response[response.find(":")+1:])
    #print(response["English"])
   # print(response["Japanese"])
    context.append({'role':'assistant', 'content':f"{response}"})
    panels.append(
        pn.Row('User:', pn.pane.Markdown(prompt, width=600)))
    
    panels.append(
        pn.Row( 
            pn.pane.PNG("static/images/ReyleneSama.png",width=64), 
            pn.pane.Markdown(response, width=600, style={'background-color': '#F6F6F6'}),
            pn.pane.Audio(f"static/audio/T{i+1}.wav"),
           # pn.pane.Markdown(response["English"], width=600, style={'background-color': '#F6F6F6'}),
           # pn.pane.Markdown(response["Japanese"], width=600, style={'background-color': '#F6F6F6'}),
        ))

    return pn.Column(*panels)

def run_chat():
    pn.extension()
    panels = [] # collect display 
    inp = pn.widgets.TextInput(value="Hi", placeholder='Enter text here…')
    button_conversation = pn.widgets.Button(name="Chat!")
    context = [ {"role":"system", "content":base}]
    interactive_conversation = pn.bind(collect_messages, button_conversation)

    dashboard = pn.Column(
        inp,
        pn.Row(button_conversation),
        pn.panel(interactive_conversation, loading_indicator=True, height=300),
    )
    dashboard.servable(title="Test")
    pn.serve(dashboard)


if __name__=="__main__":
    run_chat()