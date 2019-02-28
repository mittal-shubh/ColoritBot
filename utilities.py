import os
import sys
import time
import json
import re
import requests
from datetime import datetime
import pytz
import fbmessenger
from fbmessenger import attachments, templates, elements
from fbmessenger.thread_settings import PersistentMenu, PersistentMenuItem, MessengerProfile
import algorithmia

greeting=(["hi","hey","hello","hola"])
def classify(message_text):
    msg=message_text.lower().strip()
    if(msg in greeting) or (msg=="help"):
        # Get the response
        pass
    return

def upload_image(url):
    attachment = attachments.Image(url=url, is_reusable=True)
    client = MessengerClient(page_access_token=os.environ['PAGE_ACCESS_TOKEN'])
    res = client.upload_attachment(attachment)
    return res['attachment_id']

def handlePostback(messaging_event):
    log("Inside Postback")
    payload = messaging_event["postback"]["payload"]
    title = messaging_event["postback"]["title"]
    log(payload)
    utilities.save_message(messaging_event["sender"]["id"], title, datetime.fromtimestamp(
        messaging_event['timestamp']/1000).astimezone(pytz.timezone('UTC')))
    attachment = {}
    return

def handleAttachments(messaging_event):
    log("Inside Attachments") 
    # Location, image (stickers, emojis, gifs, add photo, add image files, take a picture, like sign), add other type of files
    for file in messaging_event["message"]["attachments"]:
        attachment = {}
        if file["type"] == "location":
            pass
        elif file["type"] == "image":
            image_url = file['payload']['url']
            save_message(messaging_event["sender"]["id"], image_url, datetime.fromtimestamp(
                messaging_event['timestamp']/1000).astimezone(pytz.timezone('UTC')))
            result = algorithmia.colorit(image_url=image_url, image_path=True)
            if isinstance(result, str):
                if result == "It's not a black & white image. Provide a black & white one.":
                    log(result)
                    break
                else:
                    attachment_id = upload_image(messaging_event['url']+result)
                    log(attachment_id)
                    btn = elements.Button(
                        button_type='web_url',
                        title='Web button',
                        url='http://facebook.com'
                        )
                    attachment = attachments.Image(attachment_id=attachment_id)
                    res = templates.MediaTemplate(attachment, buttons=[btn])
                    attachment = res.to_dict()
        else:
            pass
    return attachment

def handleFreeText(messaging_event):
    # Send back the message that you don't understand him but can definitely 
    # put colors in his b&w pictures. Send me the image.
    message_text = messaging_event["message"]["text"] 
    save_message(messaging_event["sender"]["id"], message_text, datetime.fromtimestamp(
        messaging_event['timestamp']/1000).astimezone(pytz.timezone('UTC')))
    attachment = {}
    if "text" in messaging_event["message"]:
        pass
    else:
        pass
    return attachment

def log(*args):
    if args:
        message = ''
        for i, m in enumerate(args):
            message += str(m) 
            if len(args) > 1 and i < len(args)-1:
                message += ' | '
        print(message)
        sys.stdout.flush()
        return
    raise Exception('log requires atleast one argument.')

def postRequest(url, dumpData):
    log("------Sending the bot response------")
    params = {"access_token": os.environ["PAGE_ACCESS_TOKEN"]}
    headers = {"Content-Type": "application/json"}
    log(type(dumpData))
    data = json.dumps(dumpData)
    log(type(data))
    r = requests.post(url, params=params, headers=headers, data=data)
    if r.status_code == 200:
        try:
            response = r.json()
            log(response)
        except Exception as e:
            log(str(e))
    else:
        log(r.text)
    return

def save_message(user_id, message, time=None):
    log("------Saving the Message------")
    query = sql.SQL('SELECT {col} FROM user_events WHERE {ukey1} = %s AND {ukey2} = %s;').format(
        col=sql.Identifier('id'), ukey1=sql.Identifier('user_id'), ukey2=sql.Identifier('time'))
    message_id = db_ext.fetch_column(query=query, var=(user_id, time))
    if message_id:
        db_ext.update_columns('user_events', 'id', message_id[0], list(['message', message]))
    else:
        db_ext.insert_values(table="user_events", columns=["user_id", "time"], values=(user_id, time))
        save_message(user_id, message, time)
    log("------Message Saved------")
    return

def send_message(user_id, attachment):
    log("sending message to {recipient}: {text}".format(recipient=user_id, text=text))
    url = "https://graph.facebook.com/v3.1/me/messages"
    dumpData = {"recipient": {"id": user_id}}
    dumpData["message"] = attachment
    time.sleep(len(text)/100)
    postRequest(url, dumpData)

def get_part_of_day(hour):
    return (
        "this morning" if 5 <= hour <= 11
        else
        "this afternoon" if 12 <= hour <= 16
        else
        "this evening" if 17 <= hour <= 20
        else
        "tonight")

def get_gender(user_id):
    url = 'https://graph.facebook.com/v3.1/%s' %user_id
    params = {
        'access_token': os.environ["PAGE_ACCESS_TOKEN"],
        'fields': 'gender'
    }
    response = requests.get(url=url, params=params)
    if response.status_code == 200:
        response = response.json()
        if 'gender' in response:
            gender = response['gender']
        else:
            gender = None
    else:
        gender = None
    return gender

def userDetails(user_id):
    user_details_url = "https://graph.facebook.com/v2.6/%s"%user_id 
    user_details_params = {'fields':'first_name,last_name,profile_pic,email,location{location}',
    'access_token': os.environ["PAGE_ACCESS_TOKEN"]} 
    user_details = requests.get(user_details_url, user_details_params)
    if user_details.status_code == 200:
        user_details = user_details.json()
    else:
        user_details = {}
        user_details['id'] = user_id
    gender = get_gender(user_id)
    if gender:
        user_details['gender'] = gender
    log(user_details)
    return user_details

def get_user_designation(user_id, guest_name):
    gender = get_gender(user_id)
    if gender:
        if gender == 'male':
            designation = "Sir"
        if gender == 'female':
            designation = "Ma'am"
    else:
        if guest_name:
            designation = str(guest_name)
        else:
            user_details = userDetails(user_id)
            designation = user_details['first_name']
    return designation

messenger_profile_url="https://graph.facebook.com/v3.1/me/messenger_profile"
def setupGetStartedButton():
    dumpData = {"get_started": {"payload": "introduction"}}
    postRequest(messenger_profile_url, dumpData)

def openGreeting():
    dumpData = {"greeting": [{"locale":"default", "text":"Hello {{user_first_name}}, I am colorit bot. I am here to help you make your world colorful and vibrant by redrawing your black & white images. Let's get started."}]}
    postRequest(messenger_profile_url, dumpData)

def helloMenu():
    '''
        You cannot have more than 3 `menu_items` in top level
        Valid `item_type`: 'nested' | 'web_url' | 'postback'
        `nested_items`(an array of not more than 5 PersistentMenuItem) must be supplied for 
            `nested` type menu_items 
        `url` must be supplied for `web_url` type menu items
        `payload` must be supplied for `postback` type `menu_items`
        `messenger_extensions` (TRUE | FALSE) & `webview_height_ratio` (COMPACT | TALL | FULL) is 
            only valid for item type `web_url`
        len(title) <= 30
        example_item = PersistentMenuItem(item_type, title, nested_items=None, url=None, payload=None, 
            fallback_url=None, messenger_extensions=None, webview_share_button=None, webview_height_ratio=None)
    '''
    menu_item_1 = PersistentMenuItem(item_type='postback', title='Stop', payload='stop_asking')
    
    #en_menu = PersistentMenu(menu_items=[menu_item_1, menu_item_2], locale='en_US', composer_input_disabled=None)
    menu = PersistentMenu(menu_items=[menu_item_1])
    postRequest(messenger_profile_url, MessengerProfile(persistent_menus=[menu]).to_dict())