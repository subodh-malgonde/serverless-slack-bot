import requests
import json
import uuid

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from actions.models import FeedbackInvite, FeedbackAction
from accounts.models import Employee, Bot, TeamBot
from django.contrib.auth.models import User
from bot.aws_utils import publish_sns_event


def litlbot(request):
    context = {}
    context['logo_link'] = "/static/assets/img/litlbot/logo.png"
    context['bot_name'] = 'Litlbot'
    return render(request, 'landing/index.html', context)


@csrf_exempt
def slack_bot_register_auth(request, bot_name):
    bot = Bot.objects.filter(name=bot_name).first()
    if not bot:
        return HttpResponse('404')

    state = str(uuid.uuid4().hex.upper()[0:16])
    user = User.objects.create(username=state)
    if bot_name == 'edubot':
        permissions = "bot,channels:write,channels:history,reminders:write,reminders:read"
    else:
        permissions = "bot"
    url = "https://slack.com/oauth/authorize?scope=%s&client_id=%s&state=%s" % (permissions, bot.client_id, state)
    return redirect(url)


def slack_bot_oauth(request, bot_name):
    bot = Bot.objects.filter(name=bot_name).first()
    if not bot:
        return HttpResponse('404')
    
    code = request.GET['code']
    state = request.GET['state']
    state_user = User.objects.filter(username=state).first()
    if not state_user:
        return HttpResponse('You are not authorized to perform this action.')
    params = {'code': code, 'client_id': bot.client_id,
              'client_secret': bot.client_secret}
    json_response = requests.get('https://slack.com/api/oauth.access', params)
    data = json.loads(json_response.text)
    Employee.consume_bot_slack_data(data, state_user, bot)
    if bot_name == "edubot":
        render_html_file = "landing/edubot_post_add_slack.html"
    return render(request, render_html_file, {bot_name: bot.name})


@csrf_exempt
def slack_bot_hook(request, bot_name):
    bot = Bot.objects.filter(name=bot_name).first()
    if not bot:
        return HttpResponse('404')

    if not 'payload' in request.POST:
        return HttpResponse('200 okie dokie')
    
    json_data = json.loads(request.POST['payload'])
    callback_id = json_data['callback_id']
    action_type, action_id = callback_id.split(':')
    if action_type == 'edubot_poll_response':
        response_msg = FeedbackInvite.handle_edubot_poll_response(action_id, json_data)
    elif action_type == 'send_edubot_poll_confirm':
        response_msg = FeedbackAction.handle_send_edubot_poll_response(action_id, json_data, bot)
    else:
        response_msg = 'Does not compute :('
    return HttpResponse(response_msg)


@csrf_exempt
def slack_bot_events(request, bot_name):
    if request.method == "POST":
        bot = Bot.objects.filter(name=bot_name).first()
        if bot:
            body_unicode = request.body.decode('utf-8')
            event_data = json.loads(body_unicode)
            print(event_data)
            if 'challenge' in event_data and event_data['type'] == "url_verification":
                return JsonResponse({"challenge": event_data['challenge']})
            else:
                # from bot.utils import eval_teambot_events
                team_bot = TeamBot.objects.filter(bot=bot, slack_team_id=event_data['team_id']).first()
                if team_bot:
                    event = event_data['event']
                    event['team'] = event_data['team_id']
                    function_args = {
                        "token": team_bot.slack_bot_access_token,
                        "team_bot_id": team_bot.id,
                        "events": [event]
                    }
                    publish_sns_event("bot.utils.eval_teambot_events", function_args)
                    # eval_teambot_events(team_bot.slack_bot_access_token, team_bot.id, [event])
                    return HttpResponse("OK")
                else:
                    return HttpResponse("Bot does not exist", status=400)
        else:
            return HttpResponse("404 Not Found", status=404)
    else:
        return HttpResponse("Not allowed", status=403)