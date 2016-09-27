import json
from .models import OutgoingMessage
from accounts.models import Team, Employee, TeamBot
            

def respond(sc, user_id, team_id, channel_id, message, dm=True, ptype=OutgoingMessage.TEXT, attachments=None, team_bot_id=None):
    from datetime import datetime
    attachment_str = ''

    if attachments:
        attachment_str =json.dumps(attachments)

    print("%s === Responding with chat post message api call" % (datetime.now().time()))
    response = sc.api_call('chat.postMessage', channel=channel_id, text=message, attachments=attachment_str)
    print("%s === %s" % (datetime.now().time(), response))
    
    if response['ok']:
        team = Team.objects.filter(slack_team_id=team_id).first()
        employee = None
        if user_id:
            employee = Employee.objects.filter(user__username=user_id).first()
        team_bot = None
        if team_bot_id:
            team_bot = TeamBot.objects.filter(id=team_bot_id).first()
            team = team_bot.team
            
        OutgoingMessage.objects.create(team=team, prompt_type=ptype,
                                   channel=channel_id, msg_text=message,
                                   employee=employee, dm=dm, team_bot=team_bot)
    return response


def open_dm_channel(sc, user_id):
    open_channel = sc.api_call('im.open', user=user_id)
    if open_channel['ok']:
        return open_channel['channel']['id']
    else:
        print('Error opening DM channel')
        return None
