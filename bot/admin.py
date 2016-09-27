from django.contrib import admin
from .models import UserInteraction, TeamOnboarding, IncomingMessage, OutgoingMessage, TeamBotOnboarding

admin.site.register(UserInteraction)
admin.site.register(TeamOnboarding)
admin.site.register(TeamBotOnboarding)
admin.site.register(IncomingMessage)
admin.site.register(OutgoingMessage)
