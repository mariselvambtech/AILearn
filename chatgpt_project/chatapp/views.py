import os
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

try:
    import openai
except Exception:
    openai = None

# Helper to query OpenAI or echo message

def ask_openai(conversation, show_cot=False):
    if openai is None:
        # fallback: echo last user message
        return f"Echo: {conversation[-1]['content']}"
    messages = conversation.copy()
    if show_cot:
        messages.insert(0, {'role': 'system', 'content': 'Think step by step.'})
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages,
    )
    return response.choices[0].message['content']


def chat_view(request):
    conversation = request.session.get('conversation', [])
    show_cot = request.session.get('show_cot', False)
    return render(request, 'chatapp/chat.html', {
        'conversation': conversation,
        'show_cot': show_cot
    })


@require_POST
def ask_view(request):
    message = request.POST.get('message', '')
    conversation = request.session.get('conversation', [])
    conversation.append({'role': 'user', 'content': message})
    show_cot = request.session.get('show_cot', False)
    reply = ask_openai(conversation, show_cot)
    conversation.append({'role': 'assistant', 'content': reply})
    request.session['conversation'] = conversation
    return JsonResponse({'reply': reply})


def toggle_cot(request):
    show_cot = request.session.get('show_cot', False)
    request.session['show_cot'] = not show_cot
    return JsonResponse({'show_cot': not show_cot})
