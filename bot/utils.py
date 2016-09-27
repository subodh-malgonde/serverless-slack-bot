from accounts.models import Employee, get_employee, TeamBot
from .models import IncomingMessage, OutgoingMessage
from .talk import open_dm_channel, respond
from slackclient import SlackClient
from .edubot import edubot_collaborate


def is_message(event):
    return event['type'] == 'message'


def is_dm(sc, msg):
    subtype = None
    dm = False
    
    if is_message(msg):

        if 'subtype' in msg:
            subtype = msg['subtype']
            
        if msg['channel'][0] == 'D':
            dm = True
            
    return (dm, subtype)


def send_message_to_user(employee, text, attachments=None, team_bot=None):
    if team_bot:
        team = team_bot
        team_bot_id = team_bot.id
    else:
        team = employee.get_team()
        team_bot_id = None
        
    sc = team.get_slack_socket()
    dm_channel = open_dm_channel(sc, employee.user.username)
    return respond(sc, employee.user.username, team.slack_team_id, dm_channel, text, attachments=attachments, team_bot_id=team_bot_id)


def send_message_on_channel(team, channel_id, text, attachment=None, team_bot=None):
    team_bot_id = None
    if team_bot:
        team = team_bot
        team_bot_id = team_bot.id
    sc = team.get_slack_socket()
    respond(sc, None, team.slack_team_id, channel_id, text, False, OutgoingMessage.TEXT, attachments=attachment,
            team_bot_id=team_bot_id)


def classify_and_act(sc, team_bot, msg):
    if msg['type'] == 'team_join':
        Employee.acquire_slack_user(team_bot.slack_team_id, msg['user']['id'], True, team_bot)


def eval_teambot_events(token, team_bot_id, events):
    from datetime import datetime
    print("%s == Evaluating event" % (datetime.now().time()))
    team_bot = TeamBot.objects.filter(id=int(team_bot_id)).first()
    if len(events) == 0:
        return None
    sc = SlackClient(token)

    for event in events:
        dm_status, subtype = is_dm(sc, event)

        if is_message(event) and ('subtype' not in event):
            if ('user' in event) and (event['user'] != 'USLACKBOT'):
                team = team_bot.team
                save_ic_message(team, event, dm_status, team_bot)

        if is_message(event):
            #ignore your own and other bots' messages
            if ((not subtype) or (subtype not in ('bot_message', 'message_changed'))):
                if dm_status:
                    collaborate_with_user(sc, event['user'], event['team'], event['channel'], event['text'], team_bot)
            else:
                print("ignoring as echo or other bot talking")
        else:
            classify_and_act(sc, team_bot, event)


def collaborate_with_user(sc, event_user, event_team, event_channel, event_text, team_bot):
    method_call = "%s_collaborate(sc, event_user, event_team, event_channel, event_text)" % team_bot.bot.name
    exception_method_call = "%s_collaborate(sc, event_user, event_team, event_channel, 'exception')" % team_bot.bot.name
    try:
        eval(method_call)
    except:
        eval(exception_method_call)

def save_ic_message(team, msg, dm_status, team_bot=None):
    employee = get_employee(msg['user'], team.slack_team_id, team_bot)
    if employee:
        IncomingMessage.objects.create(team=team, employee=employee, dm=dm_status,
                                       channel=msg['channel'], msg_text=msg['text'], team_bot=team_bot)


def build_attachments(obj_type, obj):
    if obj_type == 'feedback':
        return build_attachment_for_feedback(obj)
    elif obj_type == 'poll':
        return build_attachment_for_poll(obj, "poll_response")
    elif obj_type == 'edubot_poll':
        return build_attachment_for_poll(obj, "edubot_poll_response")
    else:
        return None


def build_attachment_for_leaderboard(leaders):
    attachments = []
    for idx, leader in enumerate(leaders):
        attachment = {}
        attachment['title'] = "#%d - %s" %((idx+1),leader['user'].capitalize())
        attachment['color'] = '#7CD197'
        text = "%d points and %d badges earned" % (leader['points'], leader['badges'])
        attachment['text'] = text
        attachment['attachment_type'] = 'default'
        attachments.append(attachment)

    return attachments


def build_attachment_for_article(article):
    attachments = []

    attachment = {}
    attachment['author_icon'] = article.genre.icon_url
    attachment['author_name'] = article.genre.attachment_byline
    attachment['title'] = article.text
    attachment['color'] = '#7CD197'
    attachment['attachment_type'] = 'default'
    attachments.append(attachment)
        
    attachment = {}
    attachment['text'] = "Forward this to someone by replying '@username'. Type '%s' to get a new one." % (article.genre.name)
    attachment['color'] = '#ffffff'
    attachments.append(attachment)

    return attachments


def build_attachment_for_schedule(schedule):
    attachments = []
    for idx, sch in enumerate(schedule):
        attachment = {}
        attachment['title'] = "#%d - %s at %s" %((idx+1), sch['event'], sch['time'])
        attachment['color'] = '#7CD197'
        attachment['text'] = sch['match']
        attachment['attachment_type'] = 'default'
        attachments.append(attachment)
    return attachments


def build_attachment_for_feedback(fb_invite):
    attachments = []
    attachment = {}
    attachment['color'] = '#7CD197'

    fq = fb_invite.feedback
    question = fq.questions.first()
    attachment['text'] = question.text.capitalize()
    attachment['attachment_type'] = 'default'
    attachment['fallback'] = 'We are unable to present this feedback at the moment'
    attachment['callback_id'] =  "feedback:%d" % (fb_invite.id)
    actions = []
    
    for choice in question.choices.all():
        action_answer = {}
        action_answer['name'] = choice.text
        action_answer['value'] = choice.text
        action_answer['text'] = choice.text.title()
        action_answer['type'] = 'button'
        actions.append(action_answer)

    attachment['actions'] = actions
    attachments.append(attachment)
    return attachments

def build_attachment_for_poll(fb_invite, callback_text='poll_response'):
    attachments = []
    attachment = {}
    attachment['color'] = '#7CD197'

    fq = fb_invite.feedback
    question = fq.questions.first()
    attachment['text'] = question.text.capitalize()
    attachment['attachment_type'] = 'default'
    attachment['fallback'] = 'We are unable to present this poll at the moment'
    attachment['callback_id'] =  "%s:%d" % (callback_text, fb_invite.id)
    actions = []
    for choice in question.choices.all():
        action_answer = {}
        action_answer['name'] = choice.text
        action_answer['value'] = choice.text
        action_answer['text'] = choice.text.title()
        action_answer['type'] = 'button'
        actions.append(action_answer)

    attachment['actions'] = actions
    attachments.append(attachment)
    return attachments


def build_attachment_for_feedback_summary(data, summary_type='feedback'):
    attachments = []
    for period_data in data:
        attachment = {}
        attachment['title'] = period_data["question"].capitalize()
        attachment['color'] = '#7CD197'
        attachment['attachment_type'] = 'default'
        attachment_text = ""
        for choice, perc in period_data['choices'].items():
            attachment_text += "%s : %d%% \n" % (str(choice).capitalize(), perc)

        if summary_type == 'peer-review':
            attachment_text += "Total responses: %d/%d" % (period_data['total_responses'], period_data['total_asked'])

        attachment["text"] = attachment_text
        attachments.append(attachment)
    return attachments


def build_attachments_for_feedback_aspect_choice(peer_feedback_id, choices):
    attachment = {}
    attachment["text"] = "What aspect would you like to give feedback on?"
    attachment["callback_id"] = "give_feedback:%s" % peer_feedback_id
    actions = []
    for choice in choices:
        action = {
            "name": choice[0],
            "text": choice[1],
            "type": "button",
            "value": choice[0],
            "style": "primary"
        }
        actions.append(action)
    attachment["actions"] = actions
    return [attachment]

def build_attachment_for_giving_feedback_response(question):
    attachments = []
    attachment = {}
    attachment['color'] = '#7CD197'

    attachment['text'] = question.text.capitalize()
    attachment['attachment_type'] = 'default'
    attachment['fallback'] = 'We are unable to present this feedback at the moment'
    attachment['callback_id'] = "give_feedback_response:%d" % (question.id)
    actions = []

    for choice in question.choices.all():
        action_answer = {}
        action_answer['name'] = choice.text
        action_answer['value'] = choice.text
        action_answer['text'] = choice.text.title()
        action_answer['type'] = 'button'
        actions.append(action_answer)

    attachment['actions'] = actions
    attachments.append(attachment)
    return attachments


def build_attachment_for_voluntary_feedback_summary(employee):
    from actions.models import PEER_FEEDBACK_ASPECTS, SurveyResponse
    from bot.utils import get_readable_value_from_tuple
    attachments = []
    colors = ['good', 'warning', 'danger', 'default']
    num_colors = len(colors)
    i = 0
    responses = SurveyResponse.objects.filter(question__peer_feedback_action__recipient_id=employee.id)
    if responses.count() == 0:
        return [
            {
                'title': "No feedback received so far",
                'text': '',
                'color': 'warning'
            }
        ]
    aspects = set(responses.values_list('question__feedback_aspect', flat=True))
    aspects = list(aspects)
    for aspect in aspects:
        attachment = {}
        attachment['text'] = ''
        attachment['title'] = get_readable_value_from_tuple(PEER_FEEDBACK_ASPECTS, aspect)
        attachment['color'] = colors[i%num_colors]
        i += 1
        responses_per_aspect = responses.filter(question__feedback_aspect=aspect)
        fields = []
        unique_question_texts = list(set(responses_per_aspect.values_list('question__text', flat=True)))
        for question in unique_question_texts:
            responses_for_question = responses_per_aspect.filter(question__text=question)
            field = {'title':'', 'short':False}

            num_responses = responses_for_question.count()
            num_skip_responses = responses_for_question.filter(response__text__iexact="skip").count()
            num_great_responses = responses_for_question.filter(response__text__iexact="great").count()
            num_ok_responses = responses_for_question.filter(response__text__iexact="ok").count()
            num_improvement_responses = responses_for_question.filter(response__text__iexact="needs improvement").count()

            field_value = question + "\nTotal: %d" % (num_responses-num_skip_responses)

            if num_great_responses > 0:
                field_value += ', Great: %d' % num_great_responses

            if num_ok_responses > 0:
                field_value += ', OK: %d' % num_ok_responses

            if num_improvement_responses > 0:
                field_value += ', Needs Improvement: %d' % num_improvement_responses

            field['value'] = field_value
            fields.append(field)
        attachment['fields'] = fields
        attachments.append(attachment)
    return attachments


def get_readable_value_from_tuple(tupdict, key_name):
    """
        Use this in a template as follows:
        get_readable_value_from_tuple(COUNTRIES, "IN") <-- will return "India" in COUNTRIES = (("IN", "India"),)
    """
    value = ''
    try:
        value = [choice[1] for choice in tupdict if key_name in choice]
        value = value.pop()
    except:
        value = ''
    return value


def sns_test(event, context):
    import json
    import importlib
    message = event['Records'][0]['Sns']['Message']
    data = json.loads(message)
    components = data['function_name'].split(".")
    module = importlib.import_module(".".join(components[:-1]))
    func = getattr(module, components[-1])
    func(**data['args'])