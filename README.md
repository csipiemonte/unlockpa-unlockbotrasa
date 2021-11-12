# UnlockPA -  bot RASA

## Run locally

## Deploy on server
- clone this project
- open the project's folder
- edit the .env.production file with the credetential of the DB
```bash
nano .env.production
```
- build docker image
```bash
docker build . -t unlockbotrasa
```
- run rasa and rasa_actions
```
docker-compose up -d
```

- If you need to __restart the containers__:
```
docker-compose up -d --force-recreate
```

## Settings
The file [.env](.env) contains the settings for local run.  
The file [.env.production](.env.production) contains the settings for deploying with __Docker__ run. 

- Databse settings: you have to insert the __password of the db__
- CSI bot: url of bot api
- Confidence treshold: confidence used for the csi bot prediction
- Feedback_yes_no: flag to able/disable the thumbs up/down after each answer

## Use cases
### Conversazione 1

UTENTE  
(questo messaggio lo manda di default la chat quando viene aperta)  
/get_started		

RASA  
Ciao sono il bot del tuo comune. Rispondo alle domande su emergenza covid, tasse e orari.  
Il comune di Avigliana ti avvisa che: EVENTUALE AVVISO DEL COMUNE

UTENTE  
Posso usare l’automobile con persone non conviventi?

RASA   
E' possibile usare l'automobile con persone non conviventi, purché siano rispettate le stesse misure di precauzione...

## REST requests
Ad ogni messaggio sul socket viene passato il codice del comune in modo da essere completamente stateless.

- url (webhook) : https://localhost:5005/webhooks/rest/webhook
- richiesta: 

```bash
curl -i -X POST \
   -H "Content-Type:application/json" \
   -d \
'{
"sender": "test_user",
"message": "/get_started",
"metadata": {"comune":codice_comune}
}' \
 'https://localhost:5005/webhooks/rest/webhook'
```

More requests are inside the file: [tests\rest_requests.json](tests/rest_requests.json). This file has to be imported inside [Talend API Tester](https://chrome.google.com/webstore/detail/talend-api-tester-free-ed/aejoelaoggembcahagimdiliamlcdmfm?hl=en).


# Bot documentation
## Channels
Socket and Rest channel are customized to know "customData"/"metadata" with the Comune ID, so every message we know from which Comune comes.  
Customized socket channel: [channels/my_socket.py](channels/my_socket.py) (line 217: "metadata=data["customData"]")  
Customized rest channel: [channels/my_rest.py](channels/my_rest.py) (line 125: ", metadata")
### Socket 
- socketUrl: "https://localhost:5005"
- socketPath: "/socket.io/"
- customData: {"comune": codice_comune}

## Buttons 
There are two types of __buttons__ that Rasa can send to the chat:
- "buttons": they stay on the webchat, the user can click on them multiple times
- "quick replies": they are buttons that disapper from the webchat when clicked, so they can be clicked just once.
### Buttons on Socket channel
In Rasa Socket channel, all the buttons are "quick replies".  
A customization has been made in the file [channels/my_socket.py](channels/my_socket.py#L65) from line 65.

Now by default the all the buttons are "normal buttons", in the action you can define a button as "normal button" or quick replies:
```python
# normal buttons
dispatcher.utter_message(template='utter_categoria', buttons=buttons)
# quick replies
dispatcher.utter_message(text=answer_from_bot, buttons=b, buttons_type='quick_replies')
```
PAY ATTENTION: if the buttons are defined in the "domain.yml" file they will all be "normal buttons" not quick replies.

Normal buttons example: [images/buttons.gif](images/buttons.gif).  
Quick replies example: [images/quick_replies.gif](images/quick_replies.gif).


### Debug with VSCode
- Download and install VSCode
- Clone this repo
- Using VSCode open the folder of this project
- Install the conda env and requirements (explained in chapter "run locally")
- Edit debug file:  
In the debug section on the left create the launch.json file (it is created automatically).
Add these configurations:
```json
    {
            "name": "Rasa: actions",
            "envFile": "${workspaceFolder}/.env",
            "type": "python",
            "request": "launch",
            "program": "D:/miniconda3/envs/lock_bot/Scripts/rasa.exe",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "args": ["run","actions","--debug"],
            "justMyCode": false
        },
        {
            "name": "Rasa: run",
            "envFile": "${workspaceFolder}/.env",
            "type": "python",
            "request": "launch",
            "program": "D:/miniconda3/envs/lock_bot/Scripts/rasa.exe",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "args": ["run","--cors","*"],
            "justMyCode": false
        },
```

__Change the path__ D:/miniconda3/envs/lock_bot/Scripts/rasa.exe to your path to rasa, pay attenction to select the path of the right conda env if you are using it.
