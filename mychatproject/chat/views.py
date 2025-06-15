from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from openai import OpenAI
import os
import traceback
from dotenv import load_dotenv
from .models import ChatMessage
import uuid
from .forms import UserRegisterForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages



def custom_logout_view(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('login')




# Create your views here.

# Load .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)




def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created. You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})




@csrf_exempt
def chat_page(request):
    return render(request, 'chat/chat.html')


@csrf_exempt
def reset_chat(request):
    try:
        if request.user.is_authenticated:
            ChatMessage.objects.filter(user=request.user).delete()
        else:
        
            session_id = request.session.get('session_id')
            if session_id:
                ChatMessage.objects.filter(session_id = session_id).delete()
                
        request.session.flush()
        return JsonResponse({'status':'reset successful'})
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'error':'error occured'+str(e)},status=500)



@csrf_exempt
def chat_api(request):
    try:
        if request.method == 'POST':

            # if 'session_id' not in request.session:
            #     request.session['session_id'] = str(uuid.uuid4())

            # session_id = request.session['session_id']
            print(request.body)
            print(type(request.body))
            data = json.loads(request.body)
            user_message = data.get('message', '')
            use_cot = data.get('use_cot', False)

            print(request.user)
            print(type(request.user))
            if request.user.is_authenticated:
                chat_filter = {'user':request.user}
            else:
                if 'session_id' not in request.session:
                    print("inside no user")
                    print(request.session)
                    request.session['session_id']=str(uuid.uuid4())
                chat_filter = {'session_id':request.session['session_id']}

            #save user message to DB
            ChatMessage.objects.create(
                **chat_filter,
                sender = 'user',
                message = user_message
            )


            # Build messages for OpenAI API
            chat_messages = [{"role": "system", "content": "You are a helpful assistant."}]
            messages_qs = ChatMessage.objects.filter(**chat_filter).order_by('timestamp')


            for msg in messages_qs:
                role = "user" if msg.sender == "user" else "assistant"
                chat_messages.append({"role": role, "content": msg.message})
            
            # Optionally add Chain of Thought prefix if enabled
            if use_cot:
                chat_messages.append({"role": "user", "content": "Let's think step by step."})
            try:
                response =  client.chat.completions.create(
                        model="gpt-4o",  # or "gpt-3.5-turbo" if you want cheaper
                        messages=chat_messages,
                        temperature=0.7,
                        max_tokens=500,
                    )
                
                reply = response.choices[0].message.content.strip()
                #save bot reply to DB
                ChatMessage.objects.create(
                    **chat_filter,
                    sender = "bot",
                    message = reply
                )

                #build the chat history for frontend
                updated_history = ChatMessage.objects.filter(**chat_filter).order_by('timestamp')
                chat_history = [
                    {"sender": msg.sender,"message":msg.message} for msg in updated_history  
                ]

                return JsonResponse({'history': chat_history})
            except Exception as e:
                print(traceback.format_exc())
                return JsonResponse({'error':str(e)},status=500)
        else:
            return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({"error":str(e)},status=500)