from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl

from prompt_toolkit.layout.margins import (
    ConditionalMargin,
    ScrollbarMargin,
)
from prompt_toolkit.filters import (
    Condition,
)
from prompt_toolkit.widgets import (
    RadioList,
)

from prompt_toolkit.formatted_text import (
    to_formatted_text
)

class MyRadio(RadioList):
    open_character = ""
    close_character = ""
    
    def __init__(self, values, callback, default = None) -> None:
        super().__init__(values, default)
        callback(self.values[self._selected_index][0])
        #right_buffer.text = self.values[self._selected_index][0]
        
        # Key bindings.
        kb = KeyBindings()

        @kb.add("up")
        def _up(event) -> None:
            self._selected_index = max(0, self._selected_index - 1)
            callback(self.values[self._selected_index][0])
            # right_buffer.text = self.values[self._selected_index][0]

        @kb.add("down")
        def _down(event) -> None:
            self._selected_index = min(len(self.values) - 1, self._selected_index + 1)
            callback(self.values[self._selected_index][0])
            # right_buffer.text = self.values[self._selected_index][0]


        @kb.add("enter")
        @kb.add(" ")
        def _click(event) -> None:
            event.app.exit(self.values[self._selected_index])
            # self._handle_enter()
            
        self.control = FormattedTextControl(
            self._get_text_fragments, key_bindings=kb, focusable=True
        )
        self.window = Window(
            content=self.control,
            style=self.container_style,
            right_margins=[
                ConditionalMargin(
                    margin=ScrollbarMargin(display_arrows=True),
                    filter=Condition(lambda: self.show_scrollbar),
                ),
            ],
            dont_extend_height=True,
        )

    def _get_text_fragments(self) :
        result = []
        for i, value in enumerate(self.values):
            if self.multiple_selection:
                checked = value[0] in self.current_values
            else:
                checked = value[0] == self.current_value
            selected = i == self._selected_index


            style = ""
            if selected:
                style += self.selected_style
                
            if selected:
                result.append(("[SetCursorPosition]", ">"))
            else:
                result.append(("", " "))

            result.append((self.default_style, " "))
            result.extend(to_formatted_text(value[1], style=style))
            result.append(("", "\n"))

        result.pop()  # Remove last newline.
        return result
