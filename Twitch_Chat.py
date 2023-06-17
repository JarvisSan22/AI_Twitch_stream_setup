#imports 
import socket
import logging
from emoji import demojize
from datetime import datetime
import pandas as pd
import re,os,json
from GPTBOT import context,get_completion_from_messages,speak
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())



#Logging config
sock = socket.socket()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s — %(message)s',
                    datefmt='%Y-%m-%d_%H:%M:%S',
                    handlers=[logging.FileHandler('chat.log', encoding='utf-8')])


#Subtitle save 
def save_subtitle(text,save_name,split_1,split_2):
    with open(save_name,"w",encoding="utf-8") as f:
        for line in text.split(split_1):
            if split_2 in line:
                for sub_line in line.split(split_2):
                    f.write(sub_line+"\n")
            else:
                f.write(line+" \n")
    f.close()


#Server chat to df 
def get_chat_dataframe(file):
    data = []

    with open(file, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n\n\n')
        
        for line in lines:
            try:
                time_logged = line.split('—')[0].strip()
                time_logged = datetime.strptime(time_logged, '%Y-%m-%d_%H:%M:%S')
                username_message = line.split('—')[1:]
                username_message = '—'.join(username_message).strip()
                username, channel, message = re.search(
                    ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', username_message
                ).groups()

                d = {
                    'dt': time_logged,
                    'channel': channel,
                    'username': username,
                    'message': message
                }
                data.append(d)
            except Exception:
                pass     
    return pd.DataFrame().from_records(data)

def AIChatListen(cfg,CONFIG_MEMORY=False,trigger_key="AICHAT",chatname="Reylene",audio=True):
    #Connect 
    sock.connect((cfg["server"],cfg["port"]))
    sock.send(f'PASS {cfg["token"]}\n'.encode('utf-8'))
    sock.send(f'NICK {cfg["nickname"]}\n'.encode('utf-8'))
    sock.send(f'JOIN {cfg["channel"]}\n'.encode('utf-8'))
    print(sock)
    #Bot up message 
    sock.send("PRIVMSG #{} :{}\r\n".format(cfg['channel'].replace("#",""),
     f"Bot:{chatname} is up and ready to take questions, use {trigger_key} to talk to {chatname}").encode("utf-8"))
    sock.send("PRIVMSG #{} :{}\r\n".format(cfg['channel'].replace("#",""),
     f"ボット:{trigger_key}が起動し、質問を受け付ける準備が整いましたので、{trigger_key}を使用して{chatname}と会話してください。").encode("utf-8"))
     


    if CONFIG_MEMORY: #Load config json.
        context=json.load(open("context.json","r"))
        context=list(context)
        from GPTBOT import base 
        context.append({"role":"system", "content":base})
    else:
        from GPTBOT import context

    while True:
        resp = sock.recv(2048).decode('utf-8')
        #Recive time 
        print(resp)
        user=resp[1:resp.find("!")]

        #Find twitch user 
        i_1=resp.find("#")
        i_2=i_1+resp[i_1:].find(" :")
        message=resp[i_2+1:]
        time=datetime.now()   
        #AI chat      
        if trigger_key in message:
            #Print user messages and time 
            print("user",user)
            print("message",message)
            print(user,message,time) 

            print("Run GPT")
            prompt=f"""
                <user>{user}
                <message>{message.replace(f"/{trigger_key}","")}
            """
            context.append({'role':'user', 'content':f"{prompt}"})
            print(len(context))
            #save questsion to subfile
            save_subtitle(prompt.replace("  ",""),"question_subfile.txt",".",",")
            save_subtitle("Thinking","eng_subfile.txt",".",",")
            save_subtitle("考え中","jp_subfiles.txt","、","。") 

            response = get_completion_from_messages(context,temperature=0.2) 
            response=response.replace("Raylene:","")
            print(response)
            #English transulation 
            eng_response=get_completion_from_messages([{"role":"user","content": f"次の文章は英語に翻訳してください。「{response}」"}])
            
                    


    
            gpt_endtime=datetime.now()
            #Twitch message reply with text 
            print("GPT Complete",gpt_endtime-time)
            #sock.send(f"{responses}".encode('utf-8'))
            sock.send("PRIVMSG #{} :{}\r\n".format(cfg['channel'].replace("#",""), "JP "+response).encode("utf-8"))
            sock.send("PRIVMSG #{} :{}\r\n".format(cfg['channel'].replace("#",""), "Eng "+eng_response).encode("utf-8"))
            #Audio loc 
            #Save responces 2 subs 

            save_subtitle(eng_response,"eng_subfile.txt",".",",")
            save_subtitle(response,"jp_subfiles.txt","、","。") 

            #AUdio speak
            if audio:
                print("Speak")
                audio_files="./static/audio/"
                i=len([f for f in os.listdir(audio_files) if ".wav" in f])
                audiofile=audio_files+f"{i+1}"
                speak(response.replace(chatname+":",""),audiofile)
                speak_endtime=datetime.now()
                print("Speach Done",speak_endtime-gpt_endtime)



            context.append({'role':'assistant', 'content':f"{response}"})

            #Save contect 
            if CONFIG_MEMORY:
                with open("context.json","w" ) as f:
                    contexts_json=json.dumps(context,indent=2, ensure_ascii=False)
                    f.write(contexts_json)



if __name__ == "__main__":
    
    cfg={
    "server" : os.getenv("server"),
    "port" : os.getenv("port"),
    "nickname" : os.getenv("port"),
    "token" :os.getenv("token"),
    "channel": os.getenv("channel"),
    }
    AIChatListen(cfg,CONFIG_MEMORY=False,audio=False)