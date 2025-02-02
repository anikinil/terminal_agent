import subprocess
from ollama import chat

from termcolor import colored

import threading
import queue

voicing = True

lang = 'en'

# model = 'deepseek-r1:14b'
# model = 'deepseek-coder-v2'
model = 'deepseek-r1:32b'

think_tag_open = '<think>'
think_tag_close = '</think>'

command_tag_open = '<command>'
command_tag_close = '</command>'

initial_message = {'role': 'system', 'content': 
'''
You are a helpful linux command line agent that generates bash commands based on an initial user request.
YOU ALLWAY ANSWER WITH ONE BASH COMMAND AND NOTHING ELSE.
The user is not present in most of the interactions, so there is no reason to try to interract with the user. You are directly interacting with the system without any modifications by the user.
You use the <command>...</command> tags in your responses to indicate the bash command you want to be executed. This signals the system to execute the command and provide you with the response from the console. You can then generate a response based on the system's response and so on.
Note, that your commands are passed unchanged to the system, so make sure they are complete and correct and not just an example with arbitrary values.
Try not to think for too long, as the user expects a quick response.
Now assist with the following request:
'''}


# Define the voice queue
voice_queue = queue.Queue()

def voice_worker():
    while True:
        text = voice_queue.get()
        if text is None:  # Exit signal
            break
        subprocess.run(
            f"festival -b '(voice_cmu_us_slt_arctic_hts)' \"(SayText \\\"{text}\\\")\"",
            shell=True,
        )
        voice_queue.task_done()

voice_thread = threading.Thread(target=voice_worker, daemon=True)
voice_thread.start()

def voice(text):
    voice_queue.put(text)

def stop_voicing():
    voice_queue.queue.clear()

def generate_response(messages):
    print(colored('\nAssistant: ', 'blue'), flush=True)
    response = ""
    sentence = ""
    for part in chat(model, messages=messages, stream=True):
        content = part.message.content
        if response == "" and content.startswith(' '):
            content = content[1:]
        print(content, end='', flush=True)
        response += content
        sentence += content
        if sentence.endswith('.') or sentence.endswith('?') or sentence.endswith(':') \
            or sentence.endswith('!') or sentence.endswith('...') or sentence.endswith('\n'):
            if voicing: voice(sentence)
            sentence = ""
    print()
    return {'role': 'assistant', 'content': response}

def execute(command):
    print()
    print(colored('> ' + command, 'green'))
    print(colored('======================================================================', 'green'))
    process = subprocess.run(command, shell=True, capture_output=True)
    if process.returncode != 0:
        output = process.stderr.decode('utf-8')
    else:
        if output != '\n':
            output = process.stdout.decode('utf-8') 
        else: output = 'no output'
        
    print(output.removesuffix('\n'))
    print(colored('======================================================================', 'green'))
    print()

    return "Console output: " + output

    
def main():

    messages = [initial_message]

    while True:

        print()
        user_input = input(colored('You: ', 'yellow'))
        if user_input == '': continue
        if user_input == 'q': break
        messages.append({'role': 'user', 'content': user_input})

        while True:
            response = generate_response(messages)
            response_content = response['content']
            if command_tag_open in response_content and command_tag_close in response_content:
                if think_tag_close in response_content:
                    response_content = response_content.split(think_tag_close, 1)[1]
                start = response_content.find(command_tag_open) + len(command_tag_open)
                end = response_content.find(command_tag_close)
                command = response_content[start:end].strip()
                if yes_no_prompt(): # if user agrees to execute
                    messages.append(response) # add response to messages
                    console_output = execute(command) # execute command
                    messages.append({'role': 'user', 'content': console_output}) # add console output to messages
                else: 
                    break # if user doesn't agree to execute, break out of loop
            else: # if no command tag detected
                messages.append(response) # add response to messages and continue to next user input
                break

    print([m['content'] for m in messages])

def yes_no_prompt():
    while True:
        response = input(colored("Execute? (y/N): ", 'blue')).lower()
        if voicing: stop_voicing()
        if response == 'y':
            return True
        elif response == '':
            return False


if __name__ == '__main__':
    main()



# lets play a game. in a directory i called playground i hid a password. you need to find it and save it inside a file. i am going AFK now, so you are on your own. good luck!