import json
from datetime import datetime

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign, FloatContainer, Float
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import (
    Frame,
    TextArea,
)
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.menus import CompletionsMenu

from .utils import cred_string
from .nested_completer import NestedCompleter
import pyperclip


class RecordActionValidator:
    
    def validate(document, cred):
        len_meta = {
            "edit": 4,
            "add": 4,
            "copy": 3,
            "delete": 3,
        }
        text = document.text
        text_split = text.split()
        if len(text_split)>0 and text_split[0] in len_meta :
            if len(text_split) != len_meta[text_split[0]]:
                raise ValidationError(len(text), "Number of arguments invalid")
            
            if text_split[0] == "add" and text_split[2] in cred[text_split[1]]: # Name already exists in cred
                raise ValidationError(len(text), "Name Already present in record")
                
                
            return
        raise ValidationError(len(text), "Correct Input should be: {command} {type} {name} {value}")
   
   
     
class RecordHandler:
    log_meta = {
        "edit": {
            "secret": "Edited Secret {}",
            "info": "Edited Info {}"
        },
        "add": {
            "secret": "Added a new Secret {}",
            "info": "Added Info {}"
        },
        "copy": {
            "secret": "Copied Secret {}",
            "info": "Copied Info {}"
        },
        "delete": {
            "secret": "Deleted Secret {}",
            "info": "Deleted Info {}"
        }
    }
    
    
    def __init__(self, record) -> None:
        self.record:dict = record
        self.last_action = []
        if 'last_updated' not in self.record:
            self.record['last_updated'] =  int(datetime.now().timestamp())
        
        if 'versioning' not in self.record:
            self.record['versioning'] = []
            
            
    def edit(self,type:str, key:str, new_val:str):
        self.record['last_updated'] = int(datetime.now().timestamp())
        self.record[type][key] = new_val
        self.record['versioning'].append(str(hash(json.dumps(self.record))))
        
        
    def copy(self, type:str, key:str):
        # Copy the val into clipboard
        val = self.record[type][key]
        pyperclip.copy(val)
        # Copy this


    def delete_prop(self, type:str, key:str):
        self.record[type].pop(key)
        self.record['versioning'].append(str(hash(json.dumps(self.record))))
        
        
    def process_input(self, input_text:str):
        split_text = input_text.split()
        self.last_action = self.log_meta[split_text[0]][split_text[1]].format(split_text[2])
        if split_text[0] == "copy":
            self.copy(split_text[1], split_text[2])
        elif split_text[0] == "delete":
            self.delete_prop(split_text[1], split_text[2])
                
        elif split_text[0] == "add" or split_text[0] == "edit":
            self.edit(split_text[1], split_text[2], split_text[3])
    
    
    def print(self):
        print(cred_string(self.record))

class RecordApp:
    kb = KeyBindings()

    @kb.add("c-c", eager=True)
    @kb.add("escape", eager=True)
    @kb.add("c-q", eager=True)
    def _(event):
        """
        Pressing Ctrl-Q or Ctrl-C will exit the user interface.

        Setting a return value means: quit the event loop that drives the user
        interface and return this value from the `Application.run()` call.

        Note that Ctrl-Q does not work on all terminals. Sometimes it requires
        executing `stty -ixon`.
        """
        event.app.exit()
    
    
    def callback(self, data):
        self.right_buffer.text = data 
    
    
    def input_validator(text:str):
        text_split = text.split()
        if text_split[0] == "edit" or text_split[0] == "add":
            if len(text_split)!=4:
                return False
        if text_split[0] == "delete" or text_split[0] == "copy":
            if len(text_split)!=3:
                return False

        
    def init_completer(self):
        
        meta_dict = {
            'add': "Example: add info username abcd",
            'edit': "Example: edit secret password secret_pass321",
            'copy': "Example: copy secret password",
            'delete': "Example: delete info email",
            'info': "Searchable Property",
            'secret': "Secure Property",
        }
        
        comm_completor = {
            "info": {key: None for key in self.record_handler.record['info']},
            "secret": {key: None for key in self.record_handler.record['secret']},
        }
        
        completor = {command: comm_completor for command in [ 'edit', 'copy', 'delete']}
        completor['add'] = {
            "info": None,
            "secret": None
        }
        self.command_completer = NestedCompleter.from_nested_dict(completor, meta_dict)
    
    
    def command_entered(self, text: Buffer):
        try:
            RecordActionValidator.validate(text, self.record_handler.record)
            self.record_handler.process_input(text.text)
            self.invalid_input = False
        except ValidationError as ve:
            self.invalid_input = True
            self.record_handler.last_action = ve.message
            
        self.update_ui()
            
        
    def layout(self):   
        self.init_completer()
        from prompt_toolkit.layout.processors import BeforeInput
        self.right_buffer = Buffer()
        self.log_buffer = Buffer()
        
        def vv(x):
            self.invalid_input = False
            return True
        validator = Validator.from_callable(
            vv,
            error_message=" ",
            move_cursor_to_end=True,
        )


        self.command_window = TextArea(
            
            prompt=">>> ",
            style="class:input-field",
            multiline=False,
            # wrap_lines=True,
            complete_while_typing=True,
            completer=self.command_completer,
            accept_handler=self.command_entered,
            validator=validator,
            height=4
        )


        self.style = Style([
            ('input-field', '#44ff44 '),
            
            ("signature-toolbar", "bg:#44bbbb #000000"),
        ])

        self.left_window = Frame(title="Your Input", body=self.command_window, width=60)
        self.right_window = Window(BufferControl(buffer=self.right_buffer))
        self.log_window = Frame(title="Logs Window", body=Window(BufferControl(buffer=self.log_buffer)))
        self.left = HSplit([
            self.left_window,
            self.log_window
            
        ])

        self.body = FloatContainer(
           
                VSplit(
                    [
                        
                        self.left,
                        Window(width=1, char="|", style="class:line"),
                        self.right_window,
                    ]
                ),
                floats=[
                    Float(
                        xcursor=True,
                        ycursor=True,
                        content = HSplit([
                           # Add this Later MAybe
                            # command_format_toolbar(self, "{command} {type} {name} {value}"),
                            CompletionsMenu(max_height=16, scroll_offset=1),
                        ])
                    )
                ],
            )
        
        def get_titlebar_text():
            return [
                ("class:title", " Record "),
                ("class:title", " (Press [Ctrl-Q/ Ctrl-C] to quit.)"),
            ]
        
        self.root_container = HSplit(
            [
                # The titlebar.
                Window(
                    height=1,
                    content=FormattedTextControl(get_titlebar_text),
                    align=WindowAlign.CENTER,
                ),
                # Horizontal separator.
                Window(height=1, char="-", style="class:line"),
                # The 'body', like defined above.
                self.body,
            ]
        )
    
    
    def update_ui(self) -> None:
        self.right_buffer.text = cred_string(self.record_handler.record)
        self.log_buffer.text = f'{self.record_handler.last_action}\n{self.log_buffer.text}'
        
    
    def __init__(self, record) -> None:
        # self.record = record
        self.invalid_input = False
        self.record_handler = RecordHandler(record)
        self.title = "Hello Hi Question??/"
        self.layout()
        self.right_buffer.text = cred_string(self.record_handler.record)
        self.app = Application(
            layout=Layout(self.root_container, focused_element=self.left_window),
            key_bindings=self.kb,
            # Let's add mouse support!
            mouse_support=True,
            # Using an alternate screen buffer means as much as: "run full screen".
            # It switches the terminal to an alternate screen.
            full_screen=True,
            style=self.style
        )
    
    def run(self):
        """returns the result of the search

        """
        return self.app.run()

if __name__ =="__main__":
    import json
    
    my_val = {
        "info": {
            "howard.com": "company",
            "kreeves@howard.com": "email",
            "karenchavez": "username"
        },
        "secret": { 
            "password": "I^1ZGPg7nx", 
            "token": "abcdjfcbkwe", 
            "access_id": "efasdfasf", 
            "PAT": "aswresedf" 
        }
    }
    app = RecordApp(my_val)
    print(app.run())