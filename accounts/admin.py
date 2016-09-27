from django.contrib import admin
from .models import Company, Employee, Team, TeamEmployee, Bot, TeamBot

admin.site.register(Company)
admin.site.register(Employee)
admin.site.register(Team)
admin.site.register(TeamEmployee)
admin.site.register(Bot)
admin.site.register(TeamBot)

