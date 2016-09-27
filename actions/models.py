from django.db import models
import collections
from django.utils import timezone
from datetime import timedelta
from bot.aws_utils import publish_sns_event
from accounts.models import Employee, Team, TeamBot

FEEDBACK_TYPES = (
    ('S', 'Survey'),
    ('G', 'General'),
    ('P', 'Personality'),
    ('R', 'Review'),
    ('E', 'Edubot Poll'),
)

QUESTION_TYPES = (
    ('S', 'Single Choice'),
    ('M','Multiple Choice'),
    ('T', 'Text Answer'),
    ('P', 'Personality quiz'),
)

PEER_FEEDBACK_ASPECTS = (
    ('CM', 'Communication'),
    ('TW', 'Team Work'),
    ('LD', 'Leadership'),
    ('PO', 'Productivity'),
    ('CP', 'Creativity'),
)



# GREAT, OK, NEEDS IMPROVEMENTF

class Action(models.Model):
    title = models.CharField(max_length=50)
    atype = models.CharField(max_length=10)
    author = models.ForeignKey(Employee, related_name='author_actions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s-%s" % (self.atype, self.title)

def upload_location(instance, filename):
    return "%s/%s/%s" % (type(instance).__name__.lower(), instance.id, filename)

class FeedbackAction(Action):
    feedback_type = models.CharField(choices=FEEDBACK_TYPES,max_length=1)
    description = models.TextField()
    team = models.ForeignKey(Team, null=True, blank=True)

    def __str__(self):
        return "%s-%s" % (self.feedback_type, self.description)
    
    def is_accessible_to_employee(self, employee):
        if self.invitees.filter(employee=employee, pending=True):
            return True
        return False

    @classmethod
    def in_cool_down_limit(self, employee, feedback_type):
        last_hour = timezone.now() - timedelta(hours=1)
        
        if FeedbackAction.objects.filter(author=employee, feedback_type=feedback_type,
                                            created_at__gte=last_hour).count() >= 1:
            return False

        if FeedbackAction.objects.filter(author=employee, feedback_type=feedback_type,
                                            created_at__gte=employee.start_of_day()).count() >= 5:
            return False
        return True
        
    
    def get_response_summary(self):
        summary = {}
        summary['choices'] = []
        summary['text'] = []

        for question in self.questions.all():
            
            if question.question_type == 'T':
                text_summary = {}
                text_summary[question.text] = question.get_text_answers()
                summary['text'].append(text_summary)
            else:
                question_summary = {}
                question_summary[question.text] = collections.OrderedDict()
                choices = question.get_choices()
                question_summary[question.text]['choices'] = choices
                choice_summary = collections.OrderedDict()
                for choice in choices:
                    choice_summary[choice] = question.responses.filter(response__text=choice).count()
                question_summary[question.text]['choice_summary'] = choice_summary
                summary['choices'].append(question_summary)

        return summary
    
    def aget_response_summary(self):
        summary = {}
        for question in self.questions.all():
            if question.question_type in ('S', 'M'):
                for question_response in question.responses.all():
                    summary.setdefault(question.text, []).append(question_response.response.text)
            else:
                summary.setdefault(question.text, []).append(question.responses.first().text)
    
    @classmethod
    def handle_poll_request(cls, action_id, json_data):
        from bot.models import UserInteraction
        employee = Employee.objects.filter(pk=int(action_id)).first()
        if not employee:
            return "Something went wrong. Please try again by typing `flag`."
        selected_value = json_data['actions'][0]['value']
        if selected_value == 'no':
            return "Understood. Just type `flag` when you want to flag an issue."
        else:
            ui = UserInteraction.get_last_state(employee.user.username, employee.company.name)
            ui.state = UserInteraction.POLL_QUESTION_AWAITED
            ui.save()
            return "An issue can be a personal one like `Feeling depressed with this weeks workload`" \
                   " or one you think affects many people like `Frontend team does not like the way QAs treat their work`.\n" \
                   "All issues are flagged anonymously. Please state your issue."

    @classmethod
    def handle_send_edubot_poll_response(self, action_id, json_data, bot):
        selected_value = json_data['actions'][0]['value']
        if selected_value == "send_now":
            response_url = json_data['response_url']
            feedback_action = FeedbackAction.objects.filter(id=action_id).first()

            #todo
            publish_sns_event("bot.models.send_edubot_poll_to_students", {"feedbackaction_id": action_id, "bot_id": bot.id})
            # queue.enqueue("bot.edubot.update_poll_results", response_url=response_url, feedback_action=feedback_action)
            return "We are sending the poll to all students. Will share the results soon."
        else:
            return "Saved."


def feedback_summary_snapshot(user_id, team_id, summary_type):
    from bot.utils import build_attachment_for_feedback_summary, build_attachment_for_voluntary_feedback_summary
    if summary_type == 'feedback':
        title = 'Feedback Summary\n' \
                '_All questions have choices *Great*, *Ok*, *Needs Improvement*_'
    elif summary_type == 'peer-review':
        title = 'Peer Feedback Summary'
    
    team = Team.objects.filter(slack_team_id=team_id).first()
    employee = Employee.objects.filter(user__username=user_id).first()
    start_of_the_day = team.owner.start_of_day()
    start_of_the_week = start_of_the_day - timedelta(days=7)
    if summary_type == 'feedback':
        # feedback_queryset = FeedbackInvite.objects.filter(employee__company__name=team_id,
        #                                             pending=False, created_at__gt=start_of_the_week,
        #                                             feedback__feedback_type='S')
        return title, build_attachment_for_voluntary_feedback_summary(employee)
    elif summary_type == 'peer-review':
        feedback_queryset = FeedbackInvite.objects.filter(feedback__author=employee,
                                                    created_at__gt=start_of_the_week,
                                                    feedback__feedback_type='R')
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
    attachments = build_attachment_for_feedback_summary(feedback_summary, summary_type)
    if len(attachments) == 0:
        title += " : No feedback received so far\n Type `peer feedback` to ask for feedback from your co-workers"
    return title, attachments


class PeerFeedbackAction(Action):
    recipient = models.ForeignKey(Employee, related_name='peer_feedbacks_received')

    @classmethod
    def get_feedback_aspect_choices(cls):
        return PEER_FEEDBACK_ASPECTS

    @classmethod
    def handle_callback(cls, action_id, json_data):
        src_employee = Employee.objects.filter(user__username=json_data['user']['id']).first()
        peer_feedback = PeerFeedbackAction.objects.filter(id=action_id).first()
        if src_employee and peer_feedback:
            if src_employee.id != peer_feedback.author_id:
                return {
                    "text": "Invalid request, feedback author and responder do not match"
                }
            else:
                selected_value = json_data['actions'][0]['value']
                selected_value = selected_value.upper()
                stock_questions = SurveyQuestion.objects.filter(feedback_aspect=selected_value, feedback_request=None, peer_feedback_action=None)
                for question in stock_questions:
                    new_question = SurveyQuestion.objects.create(feedback_aspect=selected_value, peer_feedback_action=peer_feedback, text=question.text)
                    SurveyResponseChoice.objects.create(text="great", question=new_question)
                    SurveyResponseChoice.objects.create(text="ok", question=new_question)
                    SurveyResponseChoice.objects.create(text="needs improvement", question=new_question)
                    SurveyResponseChoice.objects.create(text="skip", question=new_question)
                return peer_feedback.send_peer_feedback_questions_serially()
        else:
            return {
                "text": "Invalid request, employee or feedback action does not exist"
            }


    @classmethod
    def handle_feedback_response(cls, action_id, json_data):
        selected_value = json_data['actions'][0]['value']
        question = SurveyQuestion.objects.filter(id=action_id).first()
        choice = question.choices.filter(text=selected_value.lower()).first()
        if question and choice:
            SurveyResponse.objects.create(question=question, response=choice, author=question.peer_feedback_action.author)
            return question.peer_feedback_action.send_peer_feedback_questions_serially()
        else:
            return {
                "text": "Invalid request, question or choice does not exist"
            }


class SurveyQuestion(models.Model):
    text = models.TextField()
    feedback_request = models.ForeignKey(FeedbackAction, related_name='questions', null=True)
    peer_feedback_action = models.ForeignKey(PeerFeedbackAction, related_name='questions', null=True)
    question_type = models.CharField(choices=QUESTION_TYPES, max_length=1)
    feedback_aspect = models.CharField(max_length=2, choices=PEER_FEEDBACK_ASPECTS, blank=True, null=True)

    def __str__(self):
        return self.text

    def has_choices(self):
        return self.question_type != 'T'

    def get_choices(self):
        if self.question_type == 'T':
            return []
        choices = []
        for choice in self.choices.all():
            choices.append(choice.text)
        return choices

    def get_text_answers(self):
        if self.question_type != 'T':
            return None
        answers = []
        for response in self.responses.all():
            answers.append(response.text)
        return answers

    
class SurveyResponseChoice(models.Model):
    question = models.ForeignKey(SurveyQuestion, related_name='choices')
    text = models.TextField()

    def __str__(self):
        return "%s-%s" % (self.question, self.text)

class SurveyResponse(models.Model):
    question = models.ForeignKey(SurveyQuestion, related_name='responses')
    response = models.ForeignKey(SurveyResponseChoice, blank=True, null=True)
    author = models.ForeignKey(Employee, related_name='my_survey_responses')
    text = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.response:
            return "%s-%s" % (self.response, self.author)
        else:
            return "%s-%s" % (self.text, self.author)


class FeedbackInvite(models.Model):
    feedback = models.ForeignKey(FeedbackAction, related_name='invitees')
    employee = models.ForeignKey(Employee, related_name='feedback_invites')
    pending = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def in_cool_down_limit(self, employee, feedback_type):
        limit = 5

        if feedback_type == 'S':
            limit = 2

        if employee.feedback_invites.filter(feedback__feedback_type=feedback_type,
                                            created_at__gte=employee.start_of_day()).count() >= limit:
            return False
        return True

    @classmethod
    def handle_poll_response_callback(self, invite_id, json_data):
        from bot.models import UserInteraction
        from bot.knowledge import get_try_another_texts

        invite = FeedbackInvite.objects.filter(id=invite_id).first()
        selected_value = json_data['actions'][0]['value']

        src_employee = Employee.objects.filter(user__username=json_data['user']['id']).first()
        if not invite:
            return "Ayyo..i couldn't find a matching poll"
        else:
            if src_employee != invite.employee:
                return "Ayyo..it appears this poll wasn't meant for you"

            invite.pending = False
            survey_question = invite.feedback.questions.first()
            survey_choice = survey_question.choices.filter(text=selected_value).first()
            if not survey_choice:
                return "Ayyo..the selected choice does not exist"
            SurveyResponse.objects.create(question=survey_question,
                                          response=survey_choice,
                                          author=invite.employee)
            invite.save()

            survey_question.choices.filter()
            agree_choice = survey_question.choices.filter(text='Agree').first()
            agreed_response = SurveyResponse.objects.filter(question=survey_question, response=agree_choice).count()
            total_responses = SurveyResponse.objects.filter(question=survey_question).count()
            perc = int((float(agreed_response)/float(total_responses)) * 100)

            if perc == 0:
                return "Thanks for your response.\nI suggest your team sits down and has a discussion around this issue."
            if perc > 0 and perc <= 25:
                val = "A few"
            elif perc > 25 and perc <= 50:
                val = "Some"
            else:
                val = "Most"

            original_issue = survey_question.text
            return "Thanks for your response.\n%s responders agree with the issue:\n_%s_\n" \
                "I suggest your team sits down and has a discussion around this." % (val, original_issue)
    
    @classmethod
    def handle_edubot_poll_response(self, invite_id, json_data):
        from bot.models import UserInteraction
        publish_sns_event("actions.models.handle_edubot_poll_response", {"invite_id": invite_id, "json_data": json_data})
        return "Thanks for your response"


def handle_edubot_poll_response(invite_id, json_data):
    invite = FeedbackInvite.objects.filter(id=invite_id).first()
    selected_value = json_data['actions'][0]['value']

    src_employee = Employee.objects.filter(user__username=json_data['user']['id']).first()
    if not invite:
        return "Ayyo..i couldn't find a matching poll"
    else:
        if src_employee != invite.employee:
            return "Ayyo..it appears this poll wasn't meant for you"

        invite.pending = False
        survey_question = invite.feedback.questions.first()
        survey_choice = survey_question.choices.filter(text=selected_value).first()
        if not survey_choice:
            return "Ayyo..the selected choice does not exist"
        SurveyResponse.objects.create(question=survey_question,
                                      response=survey_choice,
                                      author=invite.employee)
        invite.save()
        return "Thanks for your response"
