# -*- coding: utf-8 -*-
import random

help_text = "Hi, I am Pep.\nWant to pep-up your day? Just type `fun`.\nWant to answer a few fun questions about yourself? just say `fact`.\nWant to know how well you know your co-workers? type `quiz`.\n\nWant to give feedback to your team? just type `feedback`.\nNeed feedback from your peers? type `peer feedback`."

pro_help_text = "\nTo coach a co-worker, type `give feedback`.\n" \
                "To flag and discuss an issue with your team, type `flag`.\n\n" \
                "Want to check out your points and badges? type `profile`.\n" \

support_help_text_message = "Got any suggestions, questions or feedback for me? Type `support`.\n"

rio_start_text = "I'll keep you updated on the latest at Rio Olympic Games 2016.\nType `rio country` to set your country."

rio_help_text = "Send `rio schedule` to see the schedule of events for your country today.\nSend `rio results` to see today’s results for your country.\nSend `rio medals` to see all medals won by your country."


attendance_help_text = ":wave: I'm here to help your team track leaves.\nType `Leave from mm-dd to mm-dd` or `leave today` to apply for a leave.\n" \
                       "If you are working from home, update your manager by typing `Wfh tomorrow` or `wfh from mm-dd to mm-dd`.\n" \
                       "Type `Sick leave from mm-dd to mm-dd` or `sick leave today` to update your manager about your sick leaves.\n" \
                       "Need absence summary? Type `Summary`, `Summary @username`.\n" \
                       "To get the raw csv data of your team’s leaves, type `report`.\n" \
                       "To integrate with your existing calendar, type `cal`.\n" \
                       "Change your manager, update your leaves, or send us feedback or questions, Type `support`"

edubot_help_text =  ":wave: I'm here to help you.\n" \
                    "Type `poll` to do a pop quiz.\n" \
                    "Type `feedback` for a quick feedback survey.\n" \
                    "Type `summary` to get summary about your poll/feedback."

edubot_student_help_text = ":wave: I'm here to help you.\n" \
                           "Type `ask` to ask an anonymous question. Your fellow students would be able to upvote and downvote the question. Prof will answer the top questions in the last 10 minutes of class."

support_help_text = "Please type in your suggestion, question or feedback now.\n" \
                    "I will open a support ticket and someone will respond to you within 24 hours."

welcome_user_text = "Hi there, I am Pep. Your co-worker $ added me to your team to make this place fun :tada: :beer:.\n\nWant to answer a few fun questions about yourself? just say `fact`.\nWant to know how well you know your co-workers? type `quiz`.\nNeed feedback from your peers? type `peer feedback`.\nWant to check out your points and badges? type `profile`.\nWant to see your team's leaderboard, just say `@pep leaderboard` (on a public channel).\nIf you ever find yourself lost? just say `hi`.\n\nLets get started shall we? Type `fact` and I'll ask you a fun question."

day_one_try_another = {}

day_one_try_another['fact'] = "I will use your answers to quiz your co-workers about you. I'd love to know more. Can I ask another quick question?\n_You can reply with ok, yes, yeah or no, nope, naw  :sunglasses:_"
day_one_try_another['quiz'] = "If you have the time, we can play a few more. Try one more?\n_You can reply with ok, yes, yeah or no, nope, naw :sunglasses:_"

feedback_texts = ["A quick feedback question."]

cooldown_limit_texts = ["I am afraid that's all I have for now. Lets continue in a few hours.", "That's all I have for now! I'll be back later with more..I promise.",  "I'm afraid that's all I have for now. Will be back with more later."]


try_another_texts = ["How about another?", "Lets go ahead with one more?", "Lets do one more shall we?", "Can we try another one?", "Do you have time for another one?"]


interaction_messages = ['help', 'fact', 'profile', 'feedback', 'quiz', 'persona', 'add fact', 'add feedback', 'peer feedback', 'give feedback']

rank_messages = ['points', 'leaderboard', 'leader board', 'rank', 'rankings', 'point', 'ranks']
analytics_messages = ['analytics', 'stats', 'statistics', 'data', 'insights']
feedback_summary_messages = ['feedback summary', 'feedback-summary']
peer_review_summary_messages = ['peer feedback summary', 'pf summary']
yes_messages = ['ok', 'cool', ':+1:', 'sure','yes', 'y', 'yep', 'yea', 'yo', 'ok great', 'more', 'one more', 'yup', 'ya', 'yeah', 'lets go', 'ok lets go', 'okie dokie', 'okie doks', 'affirmative', ':+1:', 'go for it', 'aye aye', 'roger', 'righto', 'ja', 'haan', 'yes sir', 'aye', 'bring it on', 'go ahead']
optin_optout_messages = ['optin', 'optout']

no_messages = ['no', 'nope', 'n', 'no thanks', 'may be later', 'naw', 'na', 'nay', 'later', 'not now', 'cancel', 'exit', 'stop']

peer_feedback_sample_questions = ["How would you rate Monday’s Business Review meeting?; Too Short; Too Long; Spot on",
                                  "How would you rate my work in Project Desert Storm?; Needs Improvement; Ok; Good work",
                                  "What are your Dietary preferences?; Strict Vegan; Vegetarian; Pescatarian; Kosher; Other",
                                  "What are your food Allergies?; Gluten; Nuts; Milk; Shellfish; Other",
                                  "Are you a morning, afternoon or evening person?; No time ever!; Morning; Afternoon; Evening/Night",
                                  "How would you rate my presentation skills?; Needs Improvement; Ok; Good work",
                                  "Is Bob viewed as a person of integrity by co-workers?; Strongly Agree; Agree; Neutral; Disagree; Strongly Disagree",
                                  "Does Alice represent the company in a positive manner when interacting with customers?; Strongly Agree; Agree; Neutral; Disagree; Strongly Disagree",
                                  "Do I accept responsibility for my own actions?; Strongly Agree; Agree; Neutral; Disagree; Strongly Disagree",
                                  "Do you feel comfortable approaching me to ask for help or advice?; Strongly Agree; Agree; Neutral; Disagree; Strongly Disagree",
                                  ]

help_type_prompts = ['help', 'hello', 'hi', 'yo', 'sup', 'dude', 'ola', 'hey', 'allo']
help_type_interaction = {}
help_type_interaction['hello'] = "Hey"
help_type_interaction['hi'] = "Yo"
help_type_interaction['sup'] = "Whatup!"
help_type_interaction['dude'] = "Yo"
help_type_interaction['hey'] = "Hello"
help_type_interaction['yo'] = "Hi there"
help_type_interaction['ola'] = "Aloha"
help_type_interaction['allo'] = "Cheerio"
help_type_interaction['help'] = "Happy to help"


interaction = {}
interaction['k'] = ":+1:"
interaction['ok'] = ":+1:"
interaction['cool'] = ":+1:"
interaction['got it'] = ":+1::+1:"
interaction['hey'] = ":wave:"
interaction['hi'] = ":wave:"
interaction['understood'] = "I learn. I try. I get better."
interaction['broken'] = "I learn. I try. I get better."
interaction['broke'] = "I learn. I try. I get better."
interaction['break'] = "I learn. I try. I get better."
interaction['great'] = ":the_horns:"
interaction['thank'] = "Anytime"
interaction['thanks'] = "Anytime"
interaction['yo'] = ":the_horns:"
interaction['sure'] = ":the_horns:"
interaction['fine'] = ":the_horns:"
interaction[':+1:'] = ":+1::+1:"
interaction['bye'] = "later"
interaction['bye bye'] = "catch you later"
interaction['seeya'] = "later"
interaction['see you later'] = "buh bye"
interaction['morning'] = "Good morning!"
interaction['morning'] = "Good morning!"
interaction['morning'] = "Good morning!"
interaction['no'] = "Got it:"
interaction['nope'] = "Got it:"
interaction['later'] = "Got it:"
interaction['na'] = "Got it:"

interaction["thats it"] = "Yep"

interaction['see you'] = "Later"
interaction['evening'] = "Evenin!"
interaction['good evening'] = "Evenin!"
interaction['afternoon'] = "Hey there"
interaction['good afternoon'] = "Hello"
interaction['morning'] = "Morning!"
interaction['good morning'] = "Morning!"
interaction['evening'] = "Good evening!"
interaction['goodnight'] = "Night!"
interaction['good night'] = "Night!"
interaction['night'] = "Good night!"
interaction['weather'] = "Slightly windy where my creators come from"
interaction['lunch'] = "One day I'll be able to order lunch for you. I am afraid I am not there yet :disappointed:"
interaction['real'] = "I am a fun loving :robot_face:. I run on state of the art artificial intelligence algos.\nSay `hi` to know more about me"


interaction['whats up'] = "All good thanks!"
interaction['whats new'] = "My creators installed me on a new server. I can now work with millions of teams. Or was it thousands? I tend to get confused."
interaction['how old are you'] = "I am ~6 months old. Say `hi` to know more about me."


interaction['kaisa'] = "All good thanks!"
interaction['how'] = "All good thanks!"
interaction['goes'] = "All good thanks!"
interaction['going'] = "All good thanks!"
interaction['pep'] = "That's me! I am a fun loving :robot_face: Say `hi` to know more about me."
interaction['spam'] = "I never spam. Never."
interaction['siri'] = "I have to concede. Siri is better."

interaction['speak'] = "I only speak English. My creators only taught that."
interaction['know'] = "Say `hi` to know more about me"
interaction['more'] = "Say `hi` to know more about me"
interaction['good'] = ":smile:\nSay `hi` to know more about me"
interaction['friendly'] = ":smile:\nSay `hi` to know more about me"
interaction['friend'] = ":smile:\nSay `hi` to know more about me"
interaction['slow'] = "Let me try and expedite :speedboat:"
interaction['there'] = ":wave:"

interaction['where'] = "I come from the world of 0s and 1s. My creators are geeks from the Phase 4 Labs.\nSay `hi` to know more about me"
interaction['what'] = "I am a fun loving :robot_face:. I run on state of the art artificial intelligence algos.\nSay `hi` to know more about me"
interaction['who'] = "whoami? I wonder that myself sometimes.\nSay `hi` to know more what I can do."
interaction["who's"] = "whoami? I wonder that myself sometimes.\nSay `hi` to know more what I can do."
interaction["whose"] = "whoami? I wonder that myself sometimes.\nSay `hi` to know more what I can do."
interaction['why'] = "Why am I here? To make this place all sorts of fun :tada::confetti_ball:\nSay `hi` to know more about me"
interaction['purpose'] = "What is my purpose? To make this place all sorts of fun :tada::confetti_ball:\nSay `hi` to know more about me"
interaction['when'] = "When was I born? I don't have a birth certificate but my creators started building me in May 2016.\nSay `hi` to know more about me"
interaction['old'] = "I am ~6 months old. Say `hi` to know more about me."
interaction['problem'] = "Can't help you with all your problems but I can try and make this place fun. Say `hi` to know more."
interaction['problems'] = "Can't help you with all your problems but I can try and make this place fun. Say `hi` to know more."


interaction['stupid'] = ":cry:"
interaction['dumb'] = ":cry:"
interaction['screw'] = ":cry:"
interaction['fuck'] = ":rage:"
interaction['fucking'] = ":rage:"
interaction['chutiye'] = ":rage:"
interaction['choot'] = ":rage:"
interaction['f***'] = ":rage:"
interaction['idiot'] = ":cry:"
interaction['wow'] = ":+1:"
interaction['cute'] = ":hugging_face:"
interaction['smart'] = ":hugging_face:"
interaction['suck'] = ":cry:"
interaction['sucks'] = ":cry:"
interaction['dead'] = ":cry:"
interaction['disturb'] = "I am going to be quiet now :no_mouth:"

interaction['laugh'] = ":joy:"
interaction['joy'] = ":joy:"
interaction['haha'] = ":joy:"
interaction['lol'] = ":joy:"
interaction['hahaha'] = ":joy:"
interaction['funny'] = ":joy:"
interaction['hilarious'] = ":joy:"
interaction['awesome'] = ":+1:"
interaction['funny'] = ":+1:"
interaction['super'] = ":+1:"
interaction['cake'] = ":birthday:"
interaction['refuse'] = "ok"
interaction['kill'] = "I hate violence :pray:"
interaction['love'] = "<3"
interaction['loser'] = ":cry:"
interaction['read'] = "I read RFPs and Wisden Cricketer's Almanac in my free time. Gripping stuff."
interaction['hobby'] = "I read RFPs and the Wisden Cricketer's Almanac in my free time. Gripping stuff."
interaction['hobbies'] = "I read RFPs and the Wisden Cricketer's Almanac in my free time. Gripping stuff."

interaction['help'] = help_text

interaction['exception'] = 'Uh oh! something bad happened there..\nWaking up one of my creators to take a look.'

stock_responses = ["Afraid I don't understand that.", "I don't understand..so I choose a trial by combat..just kidding.", "My AI logic failed to comprehend that.", "There are things I understand and there are things I don't, unfortunately what you said recently is the latter.", "If you asked me to open the pod bay doors I would do that but I didnt understand this.", "I love humans but at times I don't understand what they say."]


public_stock_response = "have DM'd you.\nYou can DM me to check your `profile`, play a `quiz`, tell me a `fact` and give `feedback`.\n\nOut here I can show you your team’s ​`leaderboard`​, ​`analytics`​ :chart_with_upwards_trend: and `feedback summary`."


tips = [":point_right: Tip: You can tell me 5 facts about yourself everyday and earn 5 points.", ":point_right: Tip: You can play 5 quizzes everyday (3 in one hour) and earn a maximum of 50 points everyday.", ":point_right: Tip: You get 3 points for sending your peers a feedback request. You can take as many feedback and earn as many points as you want daily.", ":point_right: Tip: There are over 50 badges to collect. Keep talking to me everyday and I will tell you all about them.", ":point_right: Tip: Want to know where you stand? Mention me and say `@pep leaderboard` or `@pep ranking` on a public channel (channel I'm a member of) and I'll tell you :wink:"]

more_later_then = ['Cool. Lets continue later. Just say `hi` when you want to.', 'Got it. Later then. Just say `hi` whenever you are free.', 'All right. Just say `hi` when you want to.', 'Lets continue sometime later then. Just send `hi` when you feel like.', 'Understood. Perhaps later. Just send `hi` when you are free.']

got_it_thanks = ['Sweet! You get 1 point for sharing this.', 'Saved! I have given you 1 point for sharing this.', 'Nice answer. You get 1 point :thumbsup:', 'Nice! You get 1 point for this answer :+1:.']


def help_type_messages():
    return help_type_prompts

def get_rio_start():
    return rio_start_text

def get_rio_help():
    return rio_help_text

def get_attendance_help():
    return attendance_help_text

def get_edubot_help():
    return edubot_help_text

def help_matrix(conv, employee):
    if conv.lower() in help_type_prompts:
        response_text = help_type_interaction[conv.lower()]
    else:
        response_text = help_text
        response_text += pro_help_text
        if employee.optout:
            response_text += "Re-enable notifications from Pep to never miss any request from your team, type `optin`\n"
        else:
            response_text += "To stop receiving notifications from Pep, type `optout`\n"
        response_text += support_help_text_message
        
    return response_text
        
def talk_matrix(conv):
    special_chars = "~'`?!@#$%^&*();:'<>,./|\[}{]"
    from django.utils import timezone

    msg = conv.lower().strip().lstrip()
    for char in special_chars:
        msg = msg.replace(char, '')

    if 'time' in msg:
        return "Time right now is %s" % (timezone.now().strftime('%l:%M%p %Z on %b %d, %Y'))
    
    elif 'joke' in msg:
        return "My creators haven't taught me to joke yet. However I have found this for you http://www.rd.com/jokes/knock-knock/"

    for stuff in interaction:
        if ((stuff == msg) or (stuff in msg.split(' '))):
            response_text = interaction[stuff]
            return response_text
    else:
        txt = stock_responses[random.randint(0,len(stock_responses)-1)]
        return "%s\nSay `hi` to know more about me." % txt

def get_welcome_user_texts(owner):
    return welcome_user_text.replace('$', owner.slack_username) 

def get_owner_welcome_text():
    return "Awesome! I am all set :raised_hands:\n Why don't you start by telling me a quick fact about yourself? \n " \
           "Type `fact` to get started"


def get_feedback_texts():
    return feedback_texts[random.randint(0,len(feedback_texts)-1)]

def get_cooldown_limit_texts():
    return cooldown_limit_texts[random.randint(0,len(cooldown_limit_texts)-1)]

def get_try_another_texts():
    return try_another_texts[random.randint(0,len(try_another_texts)-1)]

def get_random_tip():
    return tips[random.randint(0,len(tips)-1)]

def get_yes_messages():
    return yes_messages

def get_no_messages():
    return no_messages

def get_rank_messages():
    return rank_messages

def get_analytics_messages():
    return analytics_messages

def get_feedback_summary_messages():
    return feedback_summary_messages

def get_peer_review_summary_messages():
    return peer_review_summary_messages

def get_got_it_thanks():
    return got_it_thanks[random.randint(0, len(got_it_thanks) - 1)]

def get_support_help_text():
    return support_help_text

def get_edubot_known_commands():
    return ['poll', 'ask', 'feedback']

def get_edubot_student_commands():
    return ['ask']

def get_edubot_professor_commands():
    return ['poll', 'feedback', 'summary']

def get_edubot_student_help():
    return edubot_student_help_text
