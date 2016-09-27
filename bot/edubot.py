from .knowledge import get_edubot_help, get_edubot_known_commands, get_edubot_student_help, \
        get_edubot_student_commands, get_edubot_professor_commands
from .models import UserInteraction, OutgoingMessage
from accounts.models import get_employee, Bot, TeamBot, Employee
from .talk import respond
import requests, json, time
from datetime import timedelta
from actions.models import FeedbackInvite, SurveyResponse

def edubot_collaborate(sc, user_id, team_id, channel_id, message):
    bot = Bot.objects.filter(name='edubot').first()
    team_bot = bot.teams.filter(slack_team_id=team_id).first()

    if user_id == 'USLACKBOT':
        return None
    message = message.lower().lstrip().strip()
    employee = get_employee(user_id, team_id)

    ui = UserInteraction.get_last_state(user_id, team_id, bot)

    if message in ['help', 'hi', 'sup', 'hello', 'hey', 'yo']:
        ui.reset()
        if employee == team_bot.owner:
            return respond(sc, user_id, team_id, channel_id, get_edubot_help(), True, OutgoingMessage.TEXT, None, team_bot.id)
        else:
            return respond(sc, user_id, team_id, channel_id, get_edubot_student_help(), True, OutgoingMessage.TEXT, None, team_bot.id)
    elif message in get_edubot_known_commands():
        ui.reset()

    if (((message in get_edubot_student_commands()) and (employee == team_bot.owner)) or ((message in get_edubot_professor_commands()) and (not (employee == team_bot.owner)))):
        res_message = 'Sorry..You are not authorized to perform this action.'
        return respond(sc, user_id, team_id, channel_id, res_message, True, OutgoingMessage.TEXT, None, team_bot.id)

    if ui.state == UserInteraction.EDUBOT_POLL_AWAITED:
        text, attachment = ui.receive_edubot_poll_question(message, team_bot)
        ui.reset()
        return respond(sc, user_id, team_id, channel_id, text, True, OutgoingMessage.TEXT, attachment, team_bot.id)
    elif ui.state == UserInteraction.EDUBOT_STUDENT_QUESTION_AWAITED:
        res_message = ui.create_and_post_on_channel(sc, team_bot, message, employee)
        ui.reset()
        return respond(sc, user_id, team_id, channel_id, res_message, True, OutgoingMessage.TEXT, None, team_bot.id)

    if message == 'exception':
        res_message = 'Something went wrong. Waking up my creators. Please bear with me till they fix this.'
        respond(sc, user_id, team_id, channel_id, res_message, True, OutgoingMessage.TEXT, None, team_bot.id)
    elif message == 'poll':
        respond(sc, user_id, team_id, channel_id, ui.send_poll_help())
    elif message == 'feedback':
        respond(sc, user_id, team_id, channel_id, ui.send_feedback_help())
    elif message == 'summary':
        text, attachments = summary_snapshot(user_id, team_id)
        respond(sc, user_id, team_id, channel_id, text, True, OutgoingMessage.TEXT, attachments)
    elif message == 'ask':
        respond(sc, user_id, team_id, channel_id, ui.send_ask_help())
    else:
        ui.reset()
        res_message = ':wave: I am afraid I did not understand. Please type `help` to know more about me.'
        respond(sc, user_id, team_id, channel_id, res_message, True, OutgoingMessage.TEXT, None, team_bot.id)

def update_poll_results(response_url, feedback_action):
    time.sleep(10)
    total_invitees = feedback_action.invitees.all().count()
    for i in range(5):
        pending_invitees = feedback_action.invitees.filter(pending=False).count()
        perc = int((float(pending_invitees)/float(total_invitees)) * 100)
        data = {}
        text = "%d%% of the students responded. \nType `summary` to see survey results." % perc
        data["text"] = text
        requests.post(response_url, data=json.dumps(data))
        time.sleep(5)

def summary_snapshot(user_id, team_id):
    from bot.utils import build_attachment_for_feedback_summary, build_attachment_for_voluntary_feedback_summary
    title = 'Poll/Feedback Summary'
    
    team = TeamBot.objects.filter(slack_team_id=team_id).first()
    employee = Employee.objects.filter(user__username=user_id).first()
    start_of_the_day = team.owner.start_of_day()
    start_of_the_week = start_of_the_day - timedelta(days=7)
    feedback_queryset = FeedbackInvite.objects.filter(feedback__author=employee,
                                                    created_at__gt=start_of_the_week,
                                                    feedback__feedback_type='E')
    if not feedback_queryset.exists():
        return "No entries so far.\n Type `poll` or `feedback` to ask for poll or feedback from your students", None
    feedback_summary = []

    for feedback_invite in feedback_queryset.all().distinct('feedback'):
        summary = {}
        question = feedback_invite.feedback.questions.first()
        total_asked = FeedbackInvite.objects.filter(feedback=feedback_invite.feedback).count()
        summary['question'] = question.text
        summary['total_asked'] = total_asked
        summary['choices'] = {}
        survey_responses = SurveyResponse.objects.filter(question=question, author__company__name=team_id)
        total_responses = survey_responses.count()
        summary['total_responses'] = total_responses
        for survey in survey_responses.distinct('response').all():
            choice_text = survey.response.text
            perc = (survey_responses.filter(response=survey.response).count() / total_responses) * 100
            summary['choices'][choice_text] = perc
        feedback_summary.append(summary)
    attachments = build_attachment_for_summary(feedback_summary, total_responses)
    if len(attachments) == 0:
        title += " : No entries so far\n Type `poll` or `feedback` to ask for poll or feedback from your students"
    return title, attachments


def build_attachment_for_summary(data, total_responses):
    attachments = []
    for period_data in data:
        attachment = {}
        attachment['title'] = period_data["question"].capitalize()
        attachment['color'] = '#7CD197'
        attachment['attachment_type'] = 'default'
        attachment_text = ""
        if not period_data['choices']:
            attachment_text += "No responses so far."
        else:
            attachment_text += "Total responses: %d\n" % total_responses
            for choice, perc in period_data['choices'].items():
                attachment_text += "%s : %d%% \n" % (str(choice).capitalize(), perc)
        attachment["text"] = attachment_text
        attachments.append(attachment)
    return attachments