from django.db import models
from django.contrib.auth.models import User

from accounts.models import Employee, Company, Team, get_employee, Bot, TeamBot
from actions.models import FeedbackAction, FeedbackInvite, PeerFeedbackAction, \
    SurveyQuestion, SurveyResponseChoice
import re

# This will keep a tab on prompts we have sent out
class OutgoingMessage(models.Model):

    FEEDBACK = 'FB'
    GAME = 'GM'
    PROMPTSET = 'PS'
    FACT = 'FC'
    TEXT = 'TX'

    PROMPT_TYPES = ((FEEDBACK, 'Feedback'),
                    (GAME, 'Game'),
                    (PROMPTSET, 'From prompt set'),
                    (FACT, 'Fact'),
                    (TEXT, 'Text response'))

    team = models.ForeignKey(Team, related_name='team_prompts')
    prompt_type = models.CharField(max_length=50, choices=PROMPT_TYPES)
    channel = models.CharField(max_length=50)
    dm = models.BooleanField(default=True)
    msg_text = models.TextField()
    employee = models.ForeignKey(Employee, related_name='user_prompts',
                                 null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    team_bot = models.ForeignKey(TeamBot, related_name='teambot_prompts', null=True, blank=True)

    def __str__(self):
        return "%s-%s" % (self.team, self.prompt_type)



#This will keep a tab on events on the channels and DMs
class IncomingMessage(models.Model):
    team = models.ForeignKey(Team, related_name='incoming_messages')
    channel = models.CharField(max_length=50)
    dm = models.BooleanField(default=True)
    employee = models.ForeignKey(Employee, related_name='user_messages')
    msg_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    team_bot = models.ForeignKey(TeamBot, related_name='ic_messages', null=True, blank=True)


    def __str__(self):
        return "%s-%s" % (self.team, self.channel)
    

    @classmethod
    def interactions_with_user_today(self, employee):
        pass #if employee.incoming_messages.filter(dm=True)

    @classmethod
    def record_message_for_interactive_message_responses(self, json_data, bot=None):
        slack_team_id = json_data['team']['id']
        team = Team.objects.filter(slack_team_id=slack_team_id).first()
        employee = get_employee(json_data['user']['id'], slack_team_id)
        team_bot = None
        if bot:
            team_bot = TeamBot.objects.filter(bot=bot, team=team).first()
        original_message = json_data['original_message']

        if not 'attachments' in original_message:
            return None
        
        attachment = original_message["attachments"][0]
        msg_text = original_message['text']
        
        if 'title' in attachment:
            msg_text += " | Attachment Title: " + attachment['title']

        if 'text' in attachment:
            msg_text += " | Attachment Text: " + attachment['text']
            
        msg_text += " | Button Value: " + json_data['actions'][0]['value']
        channel = json_data['channel']['id']
        IncomingMessage.objects.create(team=team, channel=channel, employee=employee, msg_text=msg_text, team_bot=team_bot)

    
class TeamOnboarding(models.Model):

    REGISTERED = 'RG'
    OWNER_DM_SENT = 'OD'
    GENERAL_JOINED = 'GJ'
    INTRODUCED = 'ID'

    STATES_CHOICES = ((REGISTERED, 'Registered'),
                      (OWNER_DM_SENT, 'DM sent to owner'),
                      (GENERAL_JOINED, 'public channel joined'),
                      (INTRODUCED, 'Introduced on a public channel'))

    team = models.OneToOneField(Team, related_name='onboarding_state')
    state = models.CharField(max_length=50, choices=STATES_CHOICES, default=REGISTERED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s-%s" % (self.team, self.state)
    
    @classmethod
    def get_last_state(self, team):
        state = TeamOnboarding.objects.filter(team__slack_team_id=team.slack_team_id).last()
        if not state:
            return None
        
        return state

    def send_owner_dm(self):
        self.state = self.OWNER_DM_SENT
        self.save()
        return "Hi I'm Pep! Let me walk :walking: you through the stuff that I can do \n" \
               "Lets get to know each other shall we? \n" \
               "Type `fact` to get started"

    def joined_general(self):
        self.state = self.GENERAL_JOINED
        self.save()
        

    def introduced(self):
        self.state = self.INTRODUCED
        self.save()
        return None


    def acquire_members(self, sc, team_id, channel_id):
        channel_info = sc.api_call('channels.info', channel=channel_id)
        for member in channel_info['channel']['members']:
            Employee.acquire_slack_user(team_id, member, intro=False)



class TeamBotOnboarding(models.Model):

    REGISTERED = 'RG'
    OWNER_DM_SENT = 'OD'
    GENERAL_JOINED = 'GJ'
    INTRODUCED = 'ID'

    STATES_CHOICES = ((REGISTERED, 'Registered'),
                      (OWNER_DM_SENT, 'DM sent to owner'),
                      (GENERAL_JOINED, 'public channel joined'),
                      (INTRODUCED, 'Introduced on a public channel'))

    team_bot = models.OneToOneField(TeamBot, related_name='onboarding_state')
    state = models.CharField(max_length=50, choices=STATES_CHOICES, default=REGISTERED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s-%s" % (self.team_bot, self.state)
    
    @classmethod
    def get_last_state(self, teamb):
        state = TeamBotOnboarding.objects.filter(team_bot=teamb).last()
        if not state:
            return None
        
        return state

    def send_owner_dm(self):
        self.state = self.OWNER_DM_SENT
        self.save()
        attachments=None
        text = "Hi, I am AttendanceBot. I can help you apply for " \
               "vacation or let your team know when you are sick " \
               "or working from home."
        return text, attachments

    def send_edubot_owner_dm(self):
        self.state = self.OWNER_DM_SENT
        self.save()
        text = ""
        return text

    def joined_general(self):
        self.state = self.GENERAL_JOINED
        self.save()
        

    def introduced(self):
        self.state = self.INTRODUCED
        self.save()
        return None


    def acquire_members(self, sc, team_id, channel_id):
        channel_info = sc.api_call('channels.info', channel=channel_id)
        for member in channel_info['channel']['members']:
            Employee.acquire_slack_user(team_id, member)


class UserInteraction(models.Model):

    CHILLING = 'CH'
    FEEDBACK_REQUESTED = 'FR'
    FACT_REQUESTED = 'FK'
    RESPONSE_AWAITED = 'RA'
    PERSONA_RESPONSE_AWAITED = 'PAR'
    QUIZ_REQUESTED =  'QR'
    ANSWER_AWAITED = 'AA'
    FACT_AWAITED = 'CA'
    PROFILE_REQUESTED = 'PR'
    RECOGNITION_TARGET_AWAITED = 'RTR'
    PROMPT_RESPONSE_AWAITED = 'PRA'
    TRY_ANOTHER_CONFIRMATION_AWAITED = 'CNA'
    #Customization states
    CUSTOM_FACT_AWAITED = 'CFA'
    CUSTOM_FEEDBACK_AWAITED = 'CSA'
    PEER_REVIEW_PROCESS = 'PRP'
    PEERS_LIST_AWAITED = 'PLA'
    FEEDBACK_RECIPIENT_REQUESTED = 'FRR'
    COUNTRY_REQUESTED = 'CRD'
    MANAGER_AWAITED = 'MGA'
    SUPPORT_QUERY_AWAITED = 'SQA'
    FORWARD_ARTICLE_RECEPIENT_AWAITED = 'FAPA'
    POLL_QUESTION_AWAITED = 'PQA'
    EDUBOT_POLL_AWAITED = 'EPA'
    REMINDER_CONFIRMATION_AWAITED = 'RMCA'
    EDUBOT_STUDENT_QUESTION_AWAITED = 'ESQA'

    STATES_CHOICES =  ((CHILLING, 'Chilling'),
                       (FEEDBACK_REQUESTED, 'Feedback requested'),
                       (FACT_REQUESTED, 'Fact requested'),
                       (RESPONSE_AWAITED, 'Response awaited'),
                       (QUIZ_REQUESTED, 'Quiz requested'),
                       (ANSWER_AWAITED, 'Answer awaited'),
                       (FACT_AWAITED, 'Fact awaited'),
                       (PROFILE_REQUESTED, 'Profile requested'),
                       (RECOGNITION_TARGET_AWAITED, 'Recognition target requested'),
                       (TRY_ANOTHER_CONFIRMATION_AWAITED, "Try another confirmation awaited"),
                       (CUSTOM_FACT_AWAITED, "Custom fact awaited"),
                       (CUSTOM_FEEDBACK_AWAITED, 'Custom survey question awaited'),
                       (PEER_REVIEW_PROCESS, "Peer review process"),
                       (PEERS_LIST_AWAITED, "Peers list awaited"),
                       (FEEDBACK_RECIPIENT_REQUESTED, 'Feedback recepient requested'),
                       (COUNTRY_REQUESTED, 'Country requested'),
                       (MANAGER_AWAITED, 'Manager awaited'),
                       (FORWARD_ARTICLE_RECEPIENT_AWAITED, 'Forward article recepient awaited'),
                       (POLL_QUESTION_AWAITED, 'Poll question awaited'),
                       (EDUBOT_POLL_AWAITED, 'Edubot poll question awaited'),
                       (REMINDER_CONFIRMATION_AWAITED, 'Reminder confirmation awaited'),
                       (EDUBOT_STUDENT_QUESTION_AWAITED, 'Edubot student question awaited'))

    
    employee = models.ForeignKey(Employee, related_name='interaction_state')
    state = models.CharField(max_length=50, choices=STATES_CHOICES, default=CHILLING)
    bot = models.ForeignKey(Bot, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_state = models.CharField(max_length=50, choices=STATES_CHOICES, default=CHILLING)

    def __str__(self):
        return "%s-%s" % (self.employee, self.state)


    def reset(self):
        self.state = self.CHILLING
        self.save()
    
    @classmethod
    def get_last_state(self, slack_user_id, team_id, bot=None):
        team_bot = None

        
        if bot:
            state = UserInteraction.objects.filter( \
                                employee__user__username=slack_user_id, bot=bot).last()
            team_bot = bot.teams.filter(slack_team_id=team_id).first()
        else:
            state = UserInteraction.objects.filter( \
                                                    employee__user__username=slack_user_id, bot__isnull=True).last()

        if not state:
            if bot:
                employee = get_employee(slack_user_id, team_id, team_bot)
            else:
                employee = get_employee(slack_user_id, team_id)

            if not employee:
                return None
            if bot:
                state = UserInteraction.objects.create(employee=employee, bot=bot)
            else:
                state = UserInteraction.objects.create(employee=employee)
                
        return state

    def is_chilling(self):
        return self.state == UserInteraction.CHILLING

    def tell_about_flag(self):
        text = "I can help you flag an issue affecting you anonymously.\n" \
               "I poll everyone to gauge whether it affects them as well and suggest a discussion on it.\n" \
               "Your identity is not revealed at any time."
        attachments = []
        attachment = {}
        attachment["text"] = "Do you want to log an issue?"
        attachment['color'] = 'good'
        attachment["callback_id"] = "request_poll:%s" % self.employee.id
        attachment["actions"] = [
            {
            "name": "yes",
            "text": "Yes",
            "type": "button",
            "value": "yes",
            "style": "primary"
            },
            {
            "name": "no",
            "text": "No",
            "type": "button",
            "value": "no"
            }
        ]
        attachments.append(attachment)
        return [text, attachments]

    def receive_poll_and_ask_everyone(self, message):
        self.state = self.CHILLING
        self.save()
        # todo
        # queue = django_rq.get_queue('high')
        # queue.enqueue("bot.models.send_poll_to_everyone", message, self.employee)
        return "Got it. I am sending a poll on this now to everyone. I will also suggest everyone does a discussion on it. Good luck!"

    def send_support_help_text(self):
        from bot.knowledge import get_support_help_text
        self.state = self.SUPPORT_QUERY_AWAITED
        self.save()
        return get_support_help_text()

    def send_poll_help(self):
        self.state = self.EDUBOT_POLL_AWAITED
        self.save()
        question = "Do you like the new coffee machine?; YES; NO; NEUTRAL"
        return "*Great!* Lets add a poll question.\n\n_Type in a question you'd like me to ask students and give the choices (max 3), all separated by a semi colon(;)_.\n\nLike this:\n>%s\n" % question

    def send_ask_help(self):
        self.state = self.EDUBOT_STUDENT_QUESTION_AWAITED
        self.save()
        return "*Great!* Please type the question which you want to ask."

    def send_feedback_help(self):
        self.state = self.EDUBOT_POLL_AWAITED
        self.save()
        question = "How are you finding this class?; Good; Slightly Slow; Too fast"
        return "*Great!* Lets create a feedback survey.\n\n_Please enter the question followed by choices, all separated by a semi colon(;)_.\n\nLike this:\n>%s\n" % question

    def create_and_post_on_channel(self, sc, team_bot, message, employee):
        edubot_channel_post(sc, team_bot, message, employee)
        return "I have posted your question to channel #question. You can watch your fellow students vote up/down your question"

    def receive_edubot_poll_question(self, message, team_bot):
        self.state = self.CHILLING
        self.save()
        flag, fb = create_edubot_poll(message, self.employee, team_bot)
        if not flag:
            return fb, None
        attachment = {}
        attachment["text"] = ""
        attachment["callback_id"] = "send_edubot_poll_confirm:%s" % fb.id
        attachment["actions"] = [
        {
            "name": "Send Now",
            "text": "Send Now",
            "type": "button",
            "value": "send_now",
            "style": "primary"
        },
        {
            "name": "Save for later",
            "text": "Save for later",
            "type": "button",
            "value": "save_for_later",
        }
        ]
        return "Question created. Please select option:", [attachment]

def edubot_channel_post(sc, team_bot, message, employee):
    from slackclient import SlackClient
    channels_list = sc.api_call('channels.list', exclude_archived=1)
    channel_names = [channel['name'] for channel in channels_list['channels']]
    if 'question' in channel_names:
        channel_id = '#question'
        post_on_question_channel(sc, channel_id, message)
    else:
        owner_sc = SlackClient(team_bot.owner.slack_access_token)
        msg_res = owner_sc.api_call('channels.create', name='question')
        channel_id = msg_res['channel']['id']
        mentioned_employees = extract_mentions("<!everyone>", team_bot.slack_team_id, team_bot.owner)
        if mentioned_employees:
            for employee in mentioned_employees:
                owner_sc.api_call('channels.invite', channel=channel_id, user=employee.user.username)
        post_on_question_channel(sc, channel_id, message)

def post_on_question_channel(sc, channel_id, message):
    response = sc.api_call('chat.postMessage', channel=channel_id, text=message.capitalize())
    sc.api_call('reactions.add', name='thumbsup',
                timestamp=response['ts'], channel=response['channel'])
    sc.api_call('reactions.add', name='thumbsdown',
                timestamp=response['ts'], channel=response['channel'])

def send_poll_to_everyone(message, employee):
    from .utils import send_message_to_user, build_attachments
    team = employee.get_team()
    mentioned_employees = extract_mentions("<!everyone>", team.slack_team_id, employee)
    fb = FeedbackAction.objects.create(feedback_type='P', author=employee, title="Flag Poll",
                                        atype='poll', team=team)
    message = message.strip().lstrip()
    message = message[0].upper() + message[1:]
    sq = SurveyQuestion.objects.create(text=message, feedback_request=fb, question_type='P')
    for choice in ['Agree', "Do not agree"]:
        SurveyResponseChoice.objects.create(question=sq, text=choice)

    if mentioned_employees:
        for employee in mentioned_employees:
            fb_invite = FeedbackInvite.objects.create(employee=employee, feedback=fb)
            attachments = build_attachments('poll', fb_invite)
            text = "Someone from your team has flagged an issue that is bothering them. Please take this poll and share your view.\n_Responses are saved anonymously._"
            send_message_to_user(employee, text, attachments)

def create_edubot_poll(message, employee, team_bot):
    from .utils import send_message_to_user, build_attachments
    team = employee.get_team()
    mentioned_employees = extract_mentions("<!everyone>", team.slack_team_id, employee)
    fb = FeedbackAction.objects.create(feedback_type='E', author=employee, title="Edubot Poll",
                                        atype='poll', team=team)
    message = message.strip().lstrip()
    message = message[0].upper() + message[1:]
    message = message.rstrip(";")
    if "?" in message:
        question_choices_split = message.split("?")
        if len(question_choices_split) < 2:
            return False, "Something wrong with that. Try again by typing `poll`"
        else:
            question = question_choices_split[0] + "?"
            if len(question_choices_split) > 2:
                choice_text = "?".join(question_choices_split[1:])
            else:
                choice_text = question_choices_split[1]
            choices = [choice.strip().rstrip('.') for choice in choice_text.strip(";").split(";")]
    else:
        lines = message.rstrip(';').split(";")
        if len(lines) <= 3:
            return False, "Something wrong with that. Try again by typing `poll`"
        question = lines[0].strip()
        choices = [choice.strip().rstrip('.') for choice in lines[1:]]

    if len(choices) != len(set(choices)):
        return False, "You need to give different choices. Please try again by typing `poll`"

    if len(choices) < 3:
        return False, "You need to give at least 2 choices. Try again by typing `poll`"
    else:
        sq = SurveyQuestion.objects.create(text=question, feedback_request=fb, question_type='P')
        for choice in choices:
            SurveyResponseChoice.objects.create(question=sq, text=choice)
    return (True, fb)

def send_edubot_poll_to_students(feedbackaction_id, bot_id):
    from .utils import send_message_to_user, build_attachments
    feedbackaction = FeedbackAction.objects.filter(id=feedbackaction_id).first()
    bot = Bot.objects.get(id=bot_id)
    employee = feedbackaction.author
    team = employee.get_team()
    team_bot = TeamBot.objects.filter(team=team, bot=bot).first()
    mentioned_employees = extract_mentions("<!everyone>", team_bot.slack_team_id, employee)
    if mentioned_employees:
        for employee in mentioned_employees:
            fb_invite = FeedbackInvite.objects.create(employee=employee, feedback=feedbackaction)
            attachments = build_attachments('edubot_poll', fb_invite)
            text = "Please take this poll and share your views.\n_Responses are saved anonymously._"
            send_message_to_user(employee, text, attachments, team_bot)

def extract_mentions(text, team_id, myself=None, team_bot=None):
    from bot.models import get_employee
    mentions = re.findall('<@\w+>', text.upper())
    is_everyone =  re.findall('<!everyone>', text)
    employees = []
    if is_everyone and team_id and myself:
        slack_bot_user_id = myself.get_team().slack_bot_user_id
        employees = Employee.objects.filter(company__name=team_id).exclude(user__username=slack_bot_user_id).exclude(id=myself.id).all()
        return employees
    mentions = list(set(mentions))
    for mention in mentions:
        slack_user_id = mention[2:-1]
        employee = get_employee(slack_user_id=slack_user_id, team_id=team_id, team_bot=team_bot)
        if employee:
            employees.append(employee)
    return employees

def ignore_mention(text):
    m = re.search("\<@\w+\>", text)
    if m:
        if m.start() == 0:
            clean_text = re.split(':', text[m.end():])
            if len(clean_text) > 1:
                return clean_text[1]
            else:
                return clean_text[0]
        else:
            return text
    else:
        return text

def record_message_for_interactive_message_responses(json_data, bot=None):
    IncomingMessage.record_message_for_interactive_message_responses(json_data, bot)
