from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils import timezone
import pytz
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from slackclient import SlackClient
from django.db.models.signals import post_save
import hashlib


class Company(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


# for now we will treat a user's username to be the same as the user_id in slack
class Employee(models.Model):
    user = models.OneToOneField(User, related_name='employee')
    company = models.ForeignKey(Company)
    manager = models.ForeignKey('self', null=True, blank=True, related_name='reportees')
    slack_access_token = models.CharField(max_length=100, null=True, blank=True)
    slack_username = models.CharField(max_length=100, null=True, blank=True)
    slack_tz_label = models.CharField(max_length=100, null=True, blank=True)
    slack_tz = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=30, null=True, blank=True)
    optout = models.BooleanField(default=False)
    
    def __str__(self):
        if self.slack_username:
            return self.slack_username
        else:
            return self.user.username

    def get_pep_last_interaction(self):
        from bot.models import UserInteraction
        return UserInteraction.objects.filter(employee=self, bot__isnull=True).first()

    
    def is_reportee_or_manager(self, employee):
        if self.manager == employee:
            return True
        elif self.reportees.filter(user=employee.user).first():
            return True
        else:
            return False

    def is_teammate(self, employee):
        employee_teams = employee.teams.values_list('team_id', flat=True)
        if TeamEmployee.objects.filter(team__id__in=employee_teams, employee=self).first():
            return True
        else:
            return False

    def has_access_to_profile(self, employee):
        if self == employee:
            return True
        elif self.is_reportee_or_manager(employee):
            return True
        else:
            return self.is_teammate(employee)


    def get_team(self):
        team = Team.objects.filter(slack_team_id=self.company.name).first()
        if team:
            return team
        else:
            team_bot = TeamBot.objects.filter(slack_team_id=self.company.name).first()
            if team_bot:
                return team_bot.team
            else:
                return None

    def get_presence(self, team_bot=None):
        sc = None
        if team_bot:
            sc = team_bot.get_slack_socket()
        else:
            sc = self.get_team().get_slack_socket()
        response = sc.api_call('users.getPresence', user=self.user.username)
        if response['ok']:
            return response['presence']

    def is_pro(self):
        team = self.get_team()
        if team.plan == Team.PRO:
            return True
        
        return False
        
    def get_slack_team_id(self):
        team = self.get_team()
        if team:
            return team.slack_team_id
        else:
            return None
        
    def current_time(self):
        if self.slack_tz:
            ltz = pytz.timezone(self.slack_tz)
            return timezone.now().astimezone(ltz)
        else:
            return timezone.now()

    def in_office_hours(self):
        off_days = [5, 6]
        is_today_off = self.current_time().weekday() in off_days
        return ((self.current_time().hour > 11) and
                (self.current_time().hour < 17) and (not is_today_off))


    def start_of_day(self):
        from datetime import datetime
        today = self.current_time().date()
        ltz = pytz.timezone('UTC')
        if self.slack_tz:
            ltz = pytz.timezone(self.slack_tz)
        start_of_day = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=ltz)
        return start_of_day.astimezone(pytz.timezone('UTC'))
    

    def last_interaction(self):
        if hasattr(self, 'user_messages'):
            last_ic = self.user_messages.filter(dm=True).last()

        if hasattr(self, 'user_prompts'):
            last_og = self.user_prompts.filter(dm=True).last()

        if ((not last_ic) and (not last_og)):
            return None, False

        elif (last_ic and (not last_og)):
            return last_ic, False
        
        elif (last_og and (not last_ic)):
            return last_og, True
            
        elif last_ic.created_at < last_og.created_at:
            return last_og, False
        else:
            return last_ic, True
        
    # not based on presence yet.
    # last ic/og should be at least 3 hours away
    def open_to_interact(self):
        duration_since_joined = timezone.now() - self.user.date_joined
        if duration_since_joined.seconds < 7200:
            return False

        last_interaction, no_reply = self.last_interaction()

        if not last_interaction:
            return True
        
        duration = timezone.now() - last_interaction.created_at
        
        if hasattr(self, 'interaction_state'):
            if duration.seconds > 360 and no_reply:
                self.interaction_state.reset()
                
        if duration.seconds > 10800:
            return True
        else:
            return False

    # checks whether more than 2 recognition queries have been sent in the last 24 hours
    def open_to_recognise(self):
        if self.recognition_queries.filter(created_at__gte=self.start_of_day()).count() > 2:
            return False
        else:
            return True
        
    @classmethod
    def acquire_slack_user(self, team_id, user_id, intro=False, team_bot=None):

        if user_id == 'USLACKBOT':
            return None

        team = Team.objects.filter(slack_team_id=team_id).first()
        sc = None
        
        if team:
            sc = team.get_slack_socket()
        
        if team_bot:
            sc = team_bot.get_slack_socket()
            team = team_bot.team

        if not team:
            return None
        
        user_data = sc.api_call('users.info', user=user_id)

        if user_data and user_data['ok']:

            if 'is_bot' not in user_data['user']:
                return None

            if user_data['user']['is_bot']:
                return None

            company = Company.objects.filter(name=team_id).first()

            if not company:
                return None

            user, created = User.objects.get_or_create(username=user_id)
            user.email= user_data['user']['profile']['email']
            if ('first_name' in (user_data['user']['profile']).keys()):
                user.first_name = user_data['user']['profile']['first_name']
            user.save()

            if hasattr(user, 'employee'):
                employee = user.employee
            else:
                employee = Employee.objects.create(user=user, company=company)

            employee.slack_username = user_data['user']['name']
            employee.slack_tz = user_data['user']['tz']
            employee.slack_tz_label = user_data['user']['tz_label']

            employee.save()

            if intro:
                if team_bot:
                    team_bot.introduce_to_employee(employee)
                else:
                    employee.introduce_bot()

            return employee
        else:
            print("users.info api call failed user_id: " + str(user_id) + ", team_id:" + str(team_id))
            if user_data:
                print(str(user_data))
            return None

    def introduce_bot(self):
        from bot.knowledge import get_welcome_user_texts, get_owner_welcome_text
        from bot.utils import send_message_to_user
        team = self.get_team()
        if self.id == team.owner_id:
            send_message_to_user(self, get_owner_welcome_text())
        else:
            send_message_to_user(self, get_welcome_user_texts(team.owner))

        
    #we can also create team-employee mapping here
    @classmethod
    def consume_slack_data(self, data, user_data=False, state_user=None):
        from bot.models import TeamOnboarding
        if user_data:
            team_id = data['team']['id']
            user_id = data['user']['id']
            team_name = data['team']['name']
            #consume more info if needed
            bot_user_id = None
            user_name =  data['user']['name']
            user_email = data['user']['email']
        else:
            team_name = data['team_name']
            team_id = data['team_id']
            user_id = data['user_id']
            bot_user_id = data['bot']['bot_user_id']
            bot_access_token = data['bot']['bot_access_token']
            bot_employee = None

        company, created = Company.objects.get_or_create(name=team_id)

        if state_user:
            user = User.objects.filter(username=user_id).first()
            if not user:
                state_user.username = user_id
                state_user.save()
                user = state_user
            else:
                state_user.delete()
        else:
            user, created = User.objects.get_or_create(username=user_id)

        if bot_user_id:
            bot_user, created = User.objects.get_or_create(username=bot_user_id)
            bot_employee, created = Employee.objects.get_or_create(user=bot_user, company=company)
            
        if user_data:
            user.email= user_email
            user.first_name = user_name.split(' ')[0]
            user.save()
        
        if hasattr(user, 'employee'):
            employee = user.employee
        else:
            employee = Employee.objects.create(user=user, company=company)
            
        employee.slack_access_token = data['access_token']
        employee.company = company
        employee.save()

        team = Team.objects.filter(slack_team_id=team_id).first()
        
        if not team:
            team = Team.objects.create(name=team_name, owner=employee)

        team.slack_team_id = team_id
        team.owner = employee

        if bot_user_id:
            team.slack_bot_user_id = bot_user_id
            team.slack_bot_access_token = bot_access_token
        
        team.active=True
        team.save()

        sc = team.get_slack_socket()
        user_data = sc.api_call('users.info', user=user_id)
        employee.slack_username = user_data['user']['name']
        employee.slack_tz = user_data['user']['tz']
        employee.slack_tz_label = user_data['user']['tz_label']
        employee.save()
        user.email= user_data['user']['profile']['email']
        if ('first_name' in (user_data['user']['profile']).keys()):
            user.first_name = user_data['user']['profile']['first_name']
        user.save()

        # todo
        # queue = django_rq.get_queue('high')
        # queue.enqueue("accounts.mailers.send_pep_welcome_mail", employee=employee)

        TeamOnboarding.objects.get_or_create(team=team)
        
        return user


    def set_reminder(self, bot, text, date_time):
        if bot.name.lower() == 'pep':
            team = self.get_team()
            sc = team.get_slack_socket()
            return sc.api_call("reminders.add", text=text, user=self.user.username, time=date_time.strftime("%s"))
        else:
            return None
    
    @classmethod
    def consume_bot_slack_data(self, data, state_user, bot):
        from bot.models import TeamBotOnboarding
        from bot.aws_utils import publish_sns_event
        team_name = data['team_name']
        team_id = data['team_id']
        user_id = data['user_id']
        bot_user_id = data['bot']['bot_user_id']
        bot_access_token = data['bot']['bot_access_token']
        bot_employee = None

        company, created = Company.objects.get_or_create(name=team_id)

        if state_user:
            user = User.objects.filter(username=user_id).first()
            if not user:
                state_user.username = user_id
                state_user.save()
                user = state_user
            else:
                state_user.delete()
        else:
            user, created = User.objects.get_or_create(username=user_id)

        if bot_user_id:
            bot_user, created = User.objects.get_or_create(username=bot_user_id)
            bot_employee, created = Employee.objects.get_or_create(user=bot_user, company=company)
                    
        if hasattr(user, 'employee'):
            employee = user.employee
        else:
            employee = Employee.objects.create(user=user, company=company)
            
        employee.slack_access_token = data['access_token']
        employee.company = company
        employee.save()

        team = Team.objects.filter(slack_team_id=team_id).first()

        if not team:
            team = Team.objects.create(name=team_name, slack_team_id=team_id)

        teamb, created = TeamBot.objects.get_or_create(team=team, bot=bot)
        teamb.owner = employee
        teamb.slack_team_id = team_id
        teamb.slack_bot_user_id = bot_user_id
        teamb.slack_bot_access_token = bot_access_token
        teamb.active=True
        if not teamb.digest:
            teamb.digest = hashlib.md5(team_id.encode('utf-8')).hexdigest()[:10]
        teamb.save()
            
        sc = teamb.get_slack_socket()
        user_data = sc.api_call('users.info', user=user_id)
        employee.slack_username = user_data['user']['name']
        employee.slack_tz = user_data['user']['tz']
        employee.slack_tz_label = user_data['user']['tz_label']
        employee.save()
        user.email= user_data['user']['profile']['email']
        if ('first_name' in (user_data['user']['profile']).keys()):
            user.first_name = user_data['user']['profile']['first_name']
        user.save()
        # queue = django_rq.get_queue('high')
        # send_welcome_mail(queue, bot, employee)

        publish_sns_event("accounts.models.acquire_teambot_team", {"team_bot_id": teamb.id, "intro": False})
        publish_sns_event("accounts.models.send_welcome_dm", {"team_bot_id": teamb.id, "employee_id": employee.id})

        TeamBotOnboarding.objects.get_or_create(team_bot=teamb)
        
        return user

def send_welcome_mail(queue, bot, employee):
    if bot.name == 'attendance_bot':
        welcome = "accounts.mailers.send_ab_welcome_mail"
    elif bot.name == 'edubot':
        return
        #welcome = "accounts.mailers.send_edubot_welcome_mail"
    queue.enqueue(welcome, employee=employee)


def upload_location(instance, filename):
    return "%s/%s/%s" % (type(instance).__name__.lower(), instance.employee.id, filename)
    
#for now this behaves as a slack team
class Team(models.Model):
    FREE = 'F'
    PRO = 'P'
    ENTERPRISE = 'E'
    CLOSED = 'C'

    PLAN_CHOICES = ((FREE, 'Free'),
                    (PRO, 'Pro'),
                    (ENTERPRISE, 'Enterprise'),
                    (CLOSED, 'Closed'))

    name = models.CharField(max_length=200)
    owner = models.ForeignKey(Employee, blank=True, null=True)
    slack_team_id = models.CharField(max_length=20, null=True, blank=True)
    slack_bot_user_id = models.CharField(max_length=20, null=True, blank=True)
    slack_bot_access_token = models.CharField(max_length=100, null=True, blank=True)
    plan = models.CharField(choices=PLAN_CHOICES, max_length=30, default=FREE)
    active = models.BooleanField(default=True)
    
    
    def __str__(self):
        return self.name

    def is_member(self, employee):
        team_employee_ids = TeamEmployee.objects.filter(team=self).values_list('employee',flat=True)
        employees = Employee.objects.filter(id__in=team_employee_ids)
        return (employee in employees)

    def get_slack_socket(self):
        sc = SlackClient(self.slack_bot_access_token)
        return sc

    def get_slack_bot_employee(self):
        return Employee.objects.filter(user__username=self.slack_bot_user_id).first()
    
    def in_office_hours(self):
        return self.owner.in_office_hours()

    def idle_channels(self):
        from bot.models import IncomingMessage, OutgoingMessage
        sc = self.get_slack_socket()
        channels = self.get_public_channels()
        idle_channels = []
        for channel in channels:
            recent = timezone.now() - timedelta(hours=1)
            sort_of_recent = timezone.now() - timedelta(hours=2)
            if IncomingMessage.objects.filter(channel=channel,
                    created_at__gt=recent).count() == 0:
                if OutgoingMessage.objects.filter(channel=channel,
                        created_at__gt=sort_of_recent).count() == 0:
                    idle_channels.append(channel)

        return idle_channels

    def get_public_channels(self):
        public_channels = []
        sc = self.get_slack_socket()
        channels = sc.api_call('channels.list', exclude_archived=1)
        for channel in channels['channels']:
            if channel['is_member']:
                public_channels.append(channel['id'])
        return public_channels

    def deactivate_team(self):
        self.active = False
        self.save()


class Bot(models.Model):
    name = models.CharField(max_length=30)
    client_id = models.CharField(max_length=300)
    client_secret = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
            

class TeamBot(models.Model):
    FREE = 'F'
    PRO = 'P'
    ENTERPRISE = 'E'
    CLOSED = 'C'

    PLAN_CHOICES = ((FREE, 'Free'),
                    (PRO, 'Pro'),
                    (ENTERPRISE, 'Enterprise'),
                    (CLOSED, 'Closed'))

    team = models.ForeignKey(Team, related_name='bots')
    bot = models.ForeignKey(Bot, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slack_team_id = models.CharField(max_length=20, null=True, blank=True)
    slack_bot_user_id = models.CharField(max_length=20, null=True, blank=True)
    slack_bot_access_token = models.CharField(max_length=100, null=True, blank=True)
    plan = models.CharField(choices=PLAN_CHOICES, max_length=30, default=FREE)
    active = models.BooleanField(default=True)
    owner = models.ForeignKey(Employee, null=True, blank=True)
    digest = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return "%s-%s" % (self.team, self.bot)

    def get_digest(self):
        if not self.digest:
            self.digest = hashlib.md5(self.slack_team_id.encode('utf-8')).hexdigest()[:10]
            self.save()
        return self.digest


    def get_slack_socket(self):
        sc = SlackClient(self.slack_bot_access_token)
        return sc

    
    def introduce_to_employee(self, employee):
        from bot.utils import send_message_to_user
        from bot.models import UserInteraction
        text = "Hi, I am AttendanceBot. I am here to manage your leaves.\n" \
               "Do you have a manager who approves your leaves? You can give me the @username e.g. @john.\n" \
               "If you don't have a manager, reply with NA."
        ui = UserInteraction.get_last_state(employee.user.username, self.slack_team_id, self.bot)
        ui.state = UserInteraction.MANAGER_AWAITED
        ui.save()
        send_message_to_user(employee, text, team_bot=self)

    @classmethod
    def handle_support_response(cls, employee_id, json_data, bot):
        from bot.models import UserInteraction

        employee = Employee.objects.filter(pk=int(employee_id)).first()
        if not employee:
            return "Invalid request"
        slack_team = employee.get_team()
        slack_team_id = slack_team.slack_team_id
        team_bot = TeamBot.objects.filter(bot=bot, slack_team_id=slack_team_id).first()
        response_text = ""
        if team_bot:
            selected_value = json_data['actions'][0]['value']
            ui = UserInteraction.get_last_state(employee.user.username, slack_team_id, team_bot.bot)
            if selected_value == "change_manager":
                ui.state = UserInteraction.MANAGER_AWAITED
                ui.save()
                response_text = "Can you please tell me who is your manager?\n" \
                             "You can give me the @username e.g. @john. If you don't have a manager, reply with NA."
            elif selected_value == 'delete_leaves':
                ui.state = UserInteraction.SUPPORT_QUERY_AWAITED
                ui.save()
                response_text = "Our support team would do this for you in the next 24 hours.\n" \
                        "Type dates for the original leave request `MM-DD to MM-DD`"
            else:
                response_text = ui.send_support_help_text()
            return response_text
        else:
            return "Invalid request"

    def get_public_channels(self):
        public_channels = []
        sc = self.get_slack_socket()
        channels = sc.api_call('channels.list', exclude_archived=1)
        for channel in channels['channels']:
            if channel['is_member']:
                public_channels.append(channel['id'])
        return public_channels

    def deactivate_team(self):
        self.active = False
        self.save()


class TeamEmployee(models.Model):
    team = models.ForeignKey(Team, related_name='members')
    employee = models.ForeignKey(Employee, related_name='teams')

    def __str__(self):
        return "%s-%s" % (self.team, self.employee)
        
@receiver(post_save, sender=TeamEmployee)
def team_employee_created(sender, instance, **kwargs):
    instance.subscribe_employee_to_team_feed()


@receiver(user_signed_up)
def user_signed_up_(request, user, sociallogin=None, **kwargs):
    if not Employee.objects.filter(user=user).first():
        employee = Employee.objects.create(user=user, company=Company.objects.first())


def get_employee(slack_user_id, team_id, team_bot=None):
    if team_bot:
        team_id = team_bot.slack_team_id
    employee = Employee.objects.filter(user__username=slack_user_id, company__name=team_id).first()
    if not employee:
        employee = Employee.acquire_slack_user(team_id, slack_user_id, False, team_bot)
    return employee


def introduce_bot_to_team(slack_team_id):
    team = Team.objects.filter(slack_team_id=slack_team_id).first()
    for employee in Employee.objects.filter(company__name=slack_team_id):
        if employee.id != team.owner_id:
            employee.introduce_bot()


def introduce_bot_to_owner(slack_team_id):
    team = Team.objects.filter(slack_team_id=slack_team_id).first()
    team.owner.introduce_bot()

def acquire_teambot_team(team_bot_id, intro=True):
    team_bot = TeamBot.objects.get(id=team_bot_id)
    sc = team_bot.get_slack_socket()

    response = sc.api_call('users.list')
    if 'members' in response.keys():
        users = response['members']
        for slack_user in users:
            if ('is_bot' in slack_user and slack_user['is_bot']) or ('real_name' in slack_user and slack_user['real_name'] == 'slackbot'):
                continue
            if not (team_bot.owner.user.username == slack_user['id']):
                user = User.objects.filter(username=slack_user['id']).first()
                if user:
                    print('already acquired')
                    employee = Employee.objects.filter(user=user).first()
                    if intro:
                        team_bot.introduce_to_employee(employee)
                else:
                    Employee.acquire_slack_user(team_bot.slack_team_id, slack_user['id'], intro=intro, team_bot=team_bot)
                    print('acquired')
            else:
                print('owner')
    else:
        print('inactive account')

def acquire_team_members(team):
    sc = team.get_slack_socket()

    response = sc.api_call('users.list')
    if 'members' in response.keys():
        users = response['members']
        for slack_user in users:
            if ('is_bot' in slack_user and slack_user['is_bot']) or ('real_name' in slack_user and slack_user['real_name'] == 'slackbot'):
                continue
            if not (team.owner.user.username == slack_user['id']):
                user = User.objects.filter(username=slack_user['id']).first()
                if user:
                    print('already acquired')
                    employee = Employee.objects.filter(user=user).first()
                    employee.introduce_bot()
                else:
                    Employee.acquire_slack_user(team.slack_team_id, slack_user['id'], intro=True)
                    print('acquired')
            else:
                print('owner')
        team.onboarding_state.introduced()
    else:
        print('inactive account')

def deactivate_team(team_id):
    team = Team.objects.filter(id=team_id).first()
    if team:
        team.active = False
        team.save()

def deactivate_team_bot(team_bot_id):
    team = TeamBot.objects.filter(id=team_bot_id).first()
    if team:
        team.active = False
        team.save()


def send_welcome_dm(team_bot_id, employee_id):
    from bot.utils import send_message_to_user
    team_bot = TeamBot.objects.get(id=team_bot_id)
    employee = Employee.objects.get(id=employee_id)
    text = ":wave: Hi, I am Litlbot. I am here to help you make your classroom engaging.\nSay `hi` to get started"
    send_message_to_user(employee, text, team_bot=team_bot)
