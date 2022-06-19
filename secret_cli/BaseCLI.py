from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.validation import Validator

from .completer import CustomCompleter

class BaseCLI:
    
    def __init__(self, creds, input_callback = None) -> None:
        self.creds =  creds
        self.history = InMemoryHistory()
        
        self.refresh()
        
        if input_callback:
            self.input_callback = input_callback
        else:
            self.input_callback = self.input_recieved
            
    # Is it needed?
    def refresh(self):
        self.main_commands = {
            "sync": {
                "push": None,
                "pull": None
            },
            "save": None,
            "add": None,
            "exit": None,
            "lock": None
        }
        self.row_commands = set((['copy', 'edit', 'view']))
        meta_help = {
            "drive": "Sync Record with Google Drive",
            "local": "Sync Record locally",
            "sync": "Sync Record",
            "add": "Add a new Record",
            "lock": "Lock the wallet",
            "exit": "Exit",
            "copy": "Copy the property value",
            "edit": "Edit the record/property",
            "view": "View the record/property",
            
        }
        self.completer = CustomCompleter(self.creds, main_commands=self.main_commands, meta_dict=meta_help) 
        
        self.prompt_args = {
            "message": "Secret-CLI: ",
            "completer": self.completer
        }
    

    def input_recieved(self, processed_input) -> None:
        raise NotImplementedError
        
    def process_input(self, text):
        tokens = text.split()
        if len(tokens) == 0:
            return
        processed_input = {}
        
        if tokens[0]  == "save":
            processed_input['type'] = "save"
        elif tokens[0] in self.main_commands:
            processed_input['type'] = tokens[0]
            processed_input['arg'] = tokens[1:]
            # processed_input[tokens[0]] = tokens[1:]
        else:
            processed_input['type'] = 'search' 
            processed_input['arg'] = tokens
            # if tokens[-1] in self.row_commands and tokens[-2]:
            #     processed_input['sub_type'] = tokens[-1]
            #     processed_input["arg"] = tokens[:-1]
            # else:
            #     processed_input["arg"] = tokens
        self.input_callback(processed_input)
    
    def run(self):
        def valiator(input_str):
            
            import re
            pattern1 = r'^(?:((?:sync) (?:(?:push)|(?:pull)))|(?:add)|(?:save)|(?:exit)|(?:lock))$'
            
            pattern2= r'^((?:(?:(?:[^ :]*):(?:[^ :]*) ?))+)(?:((?:copy)|(?:view)|(?:edit))|(\w*) ((?:copy)|(?:view)|(?:edit)))?$'
            z1 = re.match(pattern1, input_str)
            z2 = re.match(pattern2, input_str)
            if z1:
                return True
            if z2:
                return True
            return False
        prompt_validator = Validator.from_callable(valiator, move_cursor_to_end=True)
        
        # ! Always use PromptSession when we want to have a loop, because the `prompt` always creates a PromptSession with every call
        self.ps = PromptSession(history=self.history, auto_suggest=AutoSuggestFromHistory(), complete_while_typing=True, bottom_toolbar=self.completer.help_text, validator=prompt_validator,validate_while_typing=False)
        while True:
            try:
                text = self.ps.prompt(**self.prompt_args)
                self.completer.current_text = ""
                self.process_input(text)
                
            except KeyboardInterrupt:
                break
            
    def exit(self):
        self.app.exit()
        
    
    