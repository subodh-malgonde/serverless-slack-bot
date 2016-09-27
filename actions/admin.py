from django.contrib import admin
from .models import FeedbackAction, FeedbackInvite, \
    SurveyQuestion, SurveyResponseChoice, SurveyResponse

admin.site.register(FeedbackAction)
admin.site.register(FeedbackInvite)
admin.site.register(SurveyResponse)
admin.site.register(SurveyResponseChoice)
admin.site.register(SurveyQuestion)


