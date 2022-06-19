
import base64
import json
import os
import threading
from datetime import datetime
from base64 import b64encode,b64decode

from prompt_toolkit import prompt
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings

from prompt_toolkit.validation import Validator
from prompt_toolkit.completion import PathCompleter
 
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from prompt_toolkit.formatted_text import HTML
from cryptography.fernet import Fernet, InvalidToken

def toggle_input(prompt_text=">", initially_hidden=True):
    """Input Prompt which has a toggle to show input characters or not

    Args:
        prompt_text (str, optional): Text to be shown for the prompt. Defaults to ">".
        initially_hidden (bool, optional): Initial state of visibility for the input. Defaults to True.

    Returns:
        str: Input text from the prompt
    """

    hidden = [initially_hidden]  
    bindings = KeyBindings()

    @bindings.add("c-t")
    def _(event):
        "When Ctrl-T has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    input_text = prompt(
        prompt_text,placeholder=HTML('<style color="#888888">(Ctrl-T to toggle visibility)</style>'), rprompt="Ctrl-T to toggle visibility", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )
    return input_text


def get_path_prompt(prompt_text, **kwargs):
    """Prompt for taking OS Path as input

    Args:
        prompt_text (str): Display text when taking input
        **kwargs : extra arguments to be sent to `prompt` function

    Returns:
        str: input path from the prompt
    """
    validator = Validator.from_callable(
        os.path.isdir,
        error_message="Not a valid path to a directory",
        move_cursor_to_end=True,
    )

    return prompt(
                
                prompt_text,
                completer=PathCompleter(only_directories=True), 
                rprompt="Press Tab to get suggestions",
                validator=validator,
                validate_while_typing=True, **kwargs)

# def pretty(d, indent=0):
#     ret_string = ""
#     for key, value in d.items():
#         ret_string += ('\t' * indent + str(key) + "\n")
#         if isinstance(value, dict):
#             ret_string += pretty(value, indent+1)
#         else:
#             ret_string += ('\t' * (indent+1) + str(value) + "\n")
#     return ret_string

def cred_string(cred):
    # print(cred)
    if 'last_updated' not in cred:
        cred['last_updated'] = int(datetime.now().timestamp())
    
    if 'versioning' not in cred:
        cred['versioning'] = []
    
    cred_ret = {
        'info':cred['info'],
        # 'info':{}, # ! REMOVE IF WORKS
        'secret': cred['secret'],
        'id': cred['id'],
        'versioning': cred['versioning'],
        'last_updated': str(datetime.fromtimestamp(cred['last_updated']).strftime('%d %b %Y %H:%M:%S'))
    }
    # for key in cred['info']: # ! REMOVE IF WORKS
    #     cred_ret["info"][cred['info'][key]] = key
# ! TODO later solve the \"  problem in printing using dumps
# ! " bevomes "\ because of dumps
# Remove the escaped " if exists
    return json.dumps(cred_ret, indent=4)#.replace("\\", '') # Check if safe to do so

from inspect import _ParameterKind as ParameterKind

from prompt_toolkit.filters import (
    Condition,
    is_done,
)
from prompt_toolkit.formatted_text.base import StyleAndTextTuples
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    Window,
)

from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension

def command_format_toolbar(app, command_format):
    """
    Return the `Layout` for the signature.
    """

    def get_text_fragments() :
        result: StyleAndTextTuples = []
        # return result
        append = result.append
        Signature = "class:signature-toolbar"
        append((Signature, command_format))
        return result
    
    @Condition
    def show_toolbar()->bool:
        return app.invalid_input
    
    return ConditionalContainer(
        content=Window(
            FormattedTextControl(get_text_fragments), height=Dimension.exact(1)
        ),
        filter= ~is_done & show_toolbar,
    )
