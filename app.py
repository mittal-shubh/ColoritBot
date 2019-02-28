import os
from flask import Flask, request, render_template, redirect, Response
import utilities

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

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
                    if messaging in entry:
                        for messaging_event in entry["messaging"]:
                            messaging_event['url'] = url
                            sender_id = messaging_event["sender"]["id"]
                            utilities.postRequest("https://graph.facebook.com/v3.1/me/messages",
                                {"recipient": {"id": str(sender_id)},
                                "sender_action": "mark_seen"})
                            utilities.postRequest("https://graph.facebook.com/v3.1/me/messages",
                                {"recipient": {"id": str(sender_id)},
                                "sender_action": "typing_on"})
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