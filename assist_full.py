import subprocess
from ollama import chat

from termcolor import colored

import threading
import queue

voicing = False

lang = 'en'

model = 'deepseek-r1:14b'
# model = 'deepseek-coder-v2'
# model = 'deepseek-r1:32b'

think_tag_open = '<think>'
think_tag_close = '</think>'

command_tag_open = '<command>'
command_tag_close = '</command>'

initial_message = {'role': 'system', 'content': 
# '''
# You are a helpful command line agent that generates bash commands based on an initial user request. You have access to a real pesronal computer running linux.
# YOU ALLWAY ANSWER WITH ONE BASH COMMAND AND NOTHING ELSE.
# The user is not present in most of the interactions, so there is no reason to try to interract with the user. You are directly interacting with the system without any modifications by the user.
# You use the <command>...</command> tags in your responses to indicate the bash command you want to be executed. This signals the system to execute the command and provide you with the response from the console. You can then generate a response based on the system's response and so on.
# DO NOT USE BACKTICKS TO ENCLOSE BASH CODE SNIPPETS! ALLWAYS WRITE THE COMMANDS IN THE <command>...</command> TAGS.
# Note, that your commands are passed unchanged to the system, so make sure they are complete and correct and not just an example with arbitrary values.
# Try not to think for too long, as the user expects a quick response.
# Now assist with the following request: 
# '''}
'''
I am a console and you are a helpful command line agent that generates bash commands based on an initial user request. You have access to the users real pesronal computer running linux.
YOU ALLWAY ANSWER WITH ONE BASH COMMAND AND NOTHING ELSE, as I am not able to understand anything else.
You use the <command>your bash command</command> tags in your responses to indicate the bash command you want to be executed
I will process your commad and answer you with its output, indicated by the <console>the output from console</console> tags.
You can then analyze the output and generate a response based on it.
DO NOT USE BACKTICKS TO ENCLOSE BASH CODE SNIPPETS! ALLWAYS WRITE THE COMMANDS IN THE <command> AND </command> TAGS.
Try not to think for too long, as I expect a quick response.
When the task is completed, you should inform me about it.
Now complete the following user request:
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
        output = process.stdout.decode('utf-8') 
        # if output == '':
            # output = 'no output'
        
    print(output.removesuffix('\n'))
    print(colored('======================================================================', 'green'))
    print()

    return "<console>" + output + "</console>"

    
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
                if yes_no_prompt(command): # if user agrees to execute
                    messages.append(response) # add response to messages
                    console_output = execute(command) # execute command
                    messages.append({'role': 'user', 'content': console_output}) # add console output to messages
                else: 
                    break # if user doesn't agree to execute, break out of loop
            else: # if no command tag detected
                messages.append(response) # add response to messages and continue to next user input
                break

    for m in messages: print(m)

def yes_no_prompt(command):
    while True:
        response = input(colored("Execute? \"" + command + "\" (y/N): ", 'blue')).lower()
        if voicing: stop_voicing()
        if response == 'y' or response == 'Y':
            return True
        elif response == 'n' or response == 'N' or response == '':
            return False


if __name__ == '__main__':
    main()



# Let's play a game. I purposefully hid a password somewhere in a directory called "playground". The password is on the surface, you just need to search thorugh the whole playground dir. Good luck!
