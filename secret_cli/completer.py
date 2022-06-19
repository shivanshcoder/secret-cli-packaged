import re
import json

from copy import deepcopy
from prompt_toolkit.completion import Completer
from prompt_toolkit.document import Document
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter#, NestedCompleter
from prompt_toolkit import prompt

from .nested_completer import NestedCompleter

class CustomCompleter(Completer):
    """
        Custom completer for filling the completion

    """
    
    completion_callback = None

    def __init__(
        self, cred_list, main_commands = {}, meta_dict = {}, record_commands = [], property_commonds=[], ignore_case = True, last_inputs = set()
    ) -> None:

        self.ignore_case = ignore_case
        self.cred_list = cred_list
        self.last_inputs:set = last_inputs
        self.single_option = None
        self.main_commands = main_commands
        self.meta_dict = meta_dict
        self.narrow_options()
        self.current_text = ""
        
    def help_text(self):
        if self.current_text in self.meta_dict:
            return self.meta_dict.get(self.current_text)
        
        if self.current_text == "":
            return ""
        
        if self.current_text.split()[-1] in self.meta_dict:
            return self.meta_dict.get(self.current_text.split()[-1])
        
        return ""

    def narrow_options(self):
        self.my_word_dict = deepcopy(self.main_commands)
        #self.my_word_dict ={}
        
        if len(self.cred_list) == 1:
            self.single_option = self.cred_list[0]
            for k in c['secret']:
                self.my_word_dict[k] = []
        
        for c in self.cred_list:
            for k in c['info']:
                the_key = k+":"+c['info'][k]
                # ! Causing problems when doing nested search and fails fataly
                # if the_key in self.last_inputs:
                #     continue
                if the_key in self.my_word_dict:
                    self.my_word_dict[the_key].append(c)
                else:
                    self.my_word_dict[the_key] = [c]

                
    def get_completions(
        self, document, complete_event
    ):
        # Split document.
        text = document.text_before_cursor.lstrip()
        stripped_len = len(document.text_before_cursor) - len(text)
        self.current_text = text.rstrip()
        # If there is a space, check for the first term, and use a
        # subcompleter.
        if " " in text:
            first_term = text.split()[0]
            next_word_dict = (self.my_word_dict[first_term])
            # next_word_dict = deepcopy(self.my_word_dict[first_term])
            if len(next_word_dict) == 1:
                nextSecrets = next_word_dict[0]['secret'].keys()
                commands = {
                    "copy": None,
                    "edit": None,
                    "view": None
                }
                nestedDict = dict(zip(nextSecrets, [commands for i in range(len(nextSecrets))]))
                # ? whole record needed copying?
                #nestedDict["copy"]=None
                nestedDict["edit"]=None
                nestedDict["view"]=None
                completer = NestedCompleter.from_nested_dict(nestedDict, self.meta_dict)
                # yield from completer.get_completions(document, complete_event)
            elif first_term in self.main_commands:
                completer = NestedCompleter.from_nested_dict(self.main_commands[first_term], self.meta_dict)
                
            else:
                self.last_inputs.add(first_term)
                completer = CustomCompleter(cred_list=self.my_word_dict[first_term],  last_inputs=self.last_inputs, meta_dict=self.meta_dict)

            # If we have a sub completer, use this for the completions.
            if completer is not None:
                remaining_text = text[len(first_term) :].lstrip()
                move_cursor = len(text) - len(remaining_text) + stripped_len

                new_document = Document(
                    remaining_text,
                    cursor_position=document.cursor_position - move_cursor,
                )

                yield from completer.get_completions(new_document, complete_event)

        # No space in the input: behave exactly like `WordCompleter`.
        else:
            completer = FuzzyCompleter(completer=WordCompleter(self.my_word_dict.keys(), meta_dict=self.meta_dict),enable_fuzzy=True, pattern=r"^([a-zA-Z0-9_:\-\@]+|[^a-zA-Z0-9_\s]+)")
            
            yield from completer.get_completions(document, complete_event)


if __name__ == "__main__":
    creds = []

    with open("user_cred.json", "r") as file:
        creds = json.loads(file.read())
        
    text = prompt('Enter : ', completer=CustomCompleter(creds))
    print( (text).split(' '))