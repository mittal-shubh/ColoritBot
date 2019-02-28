import os
import pytz
from datetime import datetime
from flask import Flask, request, render_template, redirect, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)
#migrate = Migrate(app, db)

import utilities, db_ext, db_models

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'UserEvents': db_models.UserEvents}

@app.route('/', methods=['GET', 'POST'])
def webhook():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.method == 'GET':
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
            if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
                return "Verification token mismatch", 403
            return request.args["hub.challenge"], 200
        return render_template('index.html'), 200
    elif request.method == 'POST':
        try:
            url = request.base_url
            utilities.log("[Request URL]: ", url)
            data = request.get_json(force=True)
            utilities.log("[User Says]: ", data) # you may not want to log every incoming message in production, but it's good for testing
            if data["object"] == "page":
                for entry in data["entry"]:
                    if 'messaging' in entry:
                        for messaging_event in entry["messaging"]:
                            messaging_event['url'] = url
                            sender_id = str(messaging_event["sender"]["id"])
                            utilities.postRequest("https://graph.facebook.com/v3.1/me/messages",
                                {"recipient": {"id": sender_id},
                                "sender_action": "mark_seen"})
                            utilities.postRequest("https://graph.facebook.com/v3.1/me/messages",
                                {"recipient": {"id": sender_id},
                                "sender_action": "typing_on"})
                            current_message_timestamp = messaging_event['timestamp']/1000
                            last_message = db_ext.user_last_message(sender_id)
                            utilities.log(last_message)
                            if last_message:
                                last_message_timestamp = datetime.timestamp(last_message[0])
                                utilities.log(last_message_timestamp, current_message_timestamp)
                                if current_message_timestamp == last_message_timestamp:
                                    utilities.log("FB's multiple request for the same message detected!")
                                    break
                                else:
                                    db_ext.insert_values(table="user_events", columns=["user_id", "time"], values=(
                                        sender_id, datetime.fromtimestamp(current_message_timestamp).astimezone(
                                            pytz.timezone('UTC'))))
                            if messaging_event.get("message") or messaging_event.get("postback"):  
                                if messaging_event.get("postback"):
                                    attachment = utilities.handlePostback(messaging_event)
                                if messaging_event.get("message"):
                                    if "quick_reply" in messaging_event["message"]:
                                        pass
                                    elif "attachments" in messaging_event["message"]:
                                        attachment = utilities.handleAttachments(messaging_event)
                                    else:
                                        attachment = utilities.handleFreeText(messaging_event)  
                                if attachment:
                                    utilities.send_message(sender_id, attachment=attachment)
                            # Save the message
                            if messaging_event.get("delivery"):  # delivery confirmation
                                pass
                            if messaging_event.get("optin"):  # optin confirmation
                                pass
                            utilities.postRequest("https://graph.facebook.com/v3.1/me/messages",
                                {"recipient": {"id": str(sender_id)},
                                "sender_action": "typing_off"})
                    else:
                        pass
            return "ok", 200
        except Exception as e:
            utilities.log(str(e))
            return "not ok", 200

@app.route('/setup', methods=['GET'])
def setup():
    utilities.setupGetStartedButton()
    utilities.openGreeting()
    utilities.helloMenu()
    return "ok", 200

@app.route('/privacypolicy', methods=['GET'])
def privacypolicy():
    return render_template('privacy_policy.html'), 200

if __name__ == '__main__':
    app.run()