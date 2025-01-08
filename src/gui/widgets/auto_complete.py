# src/gui/widgets/auto_complete.py
"""Custom autocomplete widgets for teams and competitions."""
import tkinter as tk
from tkinter import ttk
from src.data.team_data import get_all_teams
from src.gui.theme import COLORS


class TeamAutoComplete(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self._completion_list = sorted(get_all_teams())

        # Remove style from kwargs if it exists
        style_arg = kwargs.pop('style', 'Custom.TEntry')

        # Create entry widget with style
        self.entry = ttk.Entry(self, style=style_arg, **kwargs)
        self.entry.pack(fill='x', expand=True)

        self.listbox = tk.Listbox(
            self,
            height=6,
            font=('Segoe UI', 10),
            selectmode=tk.SINGLE,
            activestyle='none',
            bg=COLORS['listbox_bg'],
            fg=COLORS['text_primary'],
            selectbackground=COLORS['listbox_select'],
            selectforeground='white',
            borderwidth=1,
            relief=tk.SOLID
        )

        # Remove duplicate entry creation
        # self.entry = ttk.Entry(self, style='Custom.TEntry', **kwargs)  # Remove this line

        # Bind events
        self.entry.bind('<KeyRelease>', self.check_input)
        self.entry.bind('<Down>', self.handle_arrow_key)
        self.entry.bind('<Up>', self.handle_arrow_key)
        self.entry.bind('<Return>', self.handle_return)

        self.listbox.bind('<Double-Button-1>', self.select_item)
        self.listbox.bind('<Return>', self.select_item)
        self.listbox.bind('<Up>', self.handle_listbox_arrow)
        self.listbox.bind('<Down>', self.handle_listbox_arrow)

        self.listbox_open = False
    def check_input(self, event):
        """Check input and update suggestions."""
        if event.keysym in ('Up', 'Down', 'Return'):
            return

        typed = self.entry.get()
        if typed == '':
            if self.listbox_open:
                self.listbox.pack_forget()
                self.listbox_open = False
        else:
            matches = [item for item in self._completion_list
                       if typed.lower() in item.lower()]

            if matches:
                if not self.listbox_open:
                    self.listbox.pack(fill='x', expand=True)
                    self.listbox_open = True

                self.listbox.delete(0, tk.END)
                for item in matches:
                    self.listbox.insert(tk.END, item)

                if self.listbox.size() > 0:
                    self.listbox.select_set(0)
            else:
                if self.listbox_open:
                    self.listbox.pack_forget()
                    self.listbox_open = False

    def handle_arrow_key(self, event):
        """Handle up/down arrow key events."""
        if not self.listbox_open:
            return

        if event.keysym == 'Down':
            self.listbox.focus_set()
            if self.listbox.size() > 0:
                self.listbox.select_clear(0, tk.END)
                self.listbox.select_set(0)
                self.listbox.see(0)
        elif event.keysym == 'Up':
            self.listbox.focus_set()
            if self.listbox.size() > 0:
                last_idx = self.listbox.size() - 1
                self.listbox.select_clear(0, tk.END)
                self.listbox.select_set(last_idx)
                self.listbox.see(last_idx)

    def handle_listbox_arrow(self, event):
        """Handle arrow key events in the listbox."""
        size = self.listbox.size()
        sel = self.listbox.curselection()

        if not sel:
            return

        index = sel[0]
        if event.keysym == 'Up' and index > 0:
            self.listbox.select_clear(index)
            index -= 1
            self.listbox.select_set(index)
            self.listbox.see(index)
        elif event.keysym == 'Down' and index < (size - 1):
            self.listbox.select_clear(index)
            index += 1
            self.listbox.select_set(index)
            self.listbox.see(index)

    def handle_return(self, event):
        """Handle return key press."""
        if self.listbox_open:
            sel = self.listbox.curselection()
            if sel:
                self.select_item()
            return 'break'

    def select_item(self, event=None):
        """Select an item from the listbox."""
        if self.listbox.curselection():
            selected = self.listbox.get(self.listbox.curselection())
            self.entry.delete(0, tk.END)
            self.entry.insert(0, selected)
            self.listbox.pack_forget()
            self.listbox_open = False
            self.entry.focus_set()

            # Trigger calculation if both teams are selected
            if hasattr(self.master, 'calculate'):
                # Get references to both team entries
                home_entry = getattr(self.master, 'home_team_entry', None)
                away_entry = getattr(self.master, 'away_team_entry', None)

                if home_entry and away_entry:
                    if home_entry.get() and away_entry.get():
                        self.master.calculate()

    def get(self):
        """Get the current value of the entry."""
        return self.entry.get()

    def set(self, value):
        """Set the value of the entry."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)

    def set_text(self, text):
        """Directly set text in the entry widget"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)


class CompetitionAutoComplete(ttk.Frame):
    """Autocomplete widget for competition selection."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self._completion_list = [
            'UEFA Champions League',
            'UEFA Europa League',
            'UEFA Conference League',
            'Premier League',
            'La Liga',
            'Bundesliga',
            'Serie A',
            'Ligue 1'
        ]

        # Create listbox with styling
        self.listbox = tk.Listbox(
            self,
            height=6,
            font=('Segoe UI', 10),
            selectmode=tk.SINGLE,
            activestyle='none',
            bg=COLORS['listbox_bg'],
            fg=COLORS['text_primary'],
            selectbackground=COLORS['listbox_select'],
            selectforeground='white',
            borderwidth=1,
            relief=tk.SOLID
        )

        # Remove style from kwargs if it exists
        style_arg = kwargs.pop('style', 'Custom.TEntry')

        # Create single entry widget with proper styling
        self.entry = ttk.Entry(self, style=style_arg, **kwargs)
        self.entry.pack(fill='x', expand=True)

        # Bind events
        self.entry.bind('<KeyRelease>', self.check_input)
        self.entry.bind('<Down>', self.handle_arrow_key)
        self.entry.bind('<Up>', self.handle_arrow_key)
        self.entry.bind('<Return>', self.handle_return)

        self.listbox.bind('<Double-Button-1>', self.select_item)
        self.listbox.bind('<Return>', self.select_item)
        self.listbox.bind('<Up>', self.handle_listbox_arrow)
        self.listbox.bind('<Down>', self.handle_listbox_arrow)

        self.listbox_open = False

    # Implement same methods as TeamAutoComplete
    check_input = TeamAutoComplete.check_input
    handle_arrow_key = TeamAutoComplete.handle_arrow_key
    handle_listbox_arrow = TeamAutoComplete.handle_listbox_arrow
    handle_return = TeamAutoComplete.handle_return
    select_item = TeamAutoComplete.select_item
    get = TeamAutoComplete.get
    set = TeamAutoComplete.set

    # Implement same methods as TeamAutoComplete
    check_input = TeamAutoComplete.check_input
    handle_arrow_key = TeamAutoComplete.handle_arrow_key
    handle_listbox_arrow = TeamAutoComplete.handle_listbox_arrow
    handle_return = TeamAutoComplete.handle_return
    select_item = TeamAutoComplete.select_item
    get = TeamAutoComplete.get
    set = TeamAutoComplete.set
