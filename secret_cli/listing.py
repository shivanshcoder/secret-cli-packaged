
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.filters import (
    Condition,
)
from prompt_toolkit.widgets import (
    Frame,
)
from prompt_toolkit.formatted_text import (
    to_formatted_text
)

from prompt_toolkit.styles import Style
from .radios import MyRadio


class ListingApp:
    kb = KeyBindings()


    @kb.add("c-c", eager=True)
    @kb.add("c-q", eager=True)
    @kb.add("escape", eager=True)
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
        
    def layout(self, values):   
        self.right_buffer = Buffer()
        
        self.radios = MyRadio(
            values=values,
            callback=self.callback
        )


        # 1. First we create the layout
        #    --------------------------
        self.style = Style([
            ('radio-selected', '#4444ff underline bold '),
        ])

        self.left_window = Frame(title="Search Results", body=self.radios, width=50)
        # self.left_window = Frame(title="Search Results", body=self.radios, width=40)
        self.right_window = Window(BufferControl(buffer=self.right_buffer))


        self.body = VSplit(
            [
                self.left_window,
                # A vertical line in the middle. We explicitly specify the width, to make
                # sure that the layout engine will not try to divide the whole width by
                # three for all these windows.
                Window(width=1, char="|", style="class:line"),
                # Display the Result buffer on the right.
                self.right_window,
            ]
        )


        def get_titlebar_text():
            return [
                ("class:title", " Search Results "),
                ("class:title", " (Press [Ctrl-Q/Ctrl-C] to quit.)"),
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
    
    def __init__(self, values) -> None:
        self.layout(values)
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
        pass
    
    def run(self):
        """returns the result of the search

        """
        return self.app.run()
    
if __name__ =="__main__":
    import json
    
    my_val = json.dumps({"Hi": {"Hello": None, "Bye":None}}, indent=4, sort_keys=True)
    values=[
        (my_val, "1. laalaaa",),
        ("2", "2. haraaaa"),
        ("3", "3. Neelaaaaaaaaaa"),
    ]
    app = ListingApp(values=values)
    print(app.run())