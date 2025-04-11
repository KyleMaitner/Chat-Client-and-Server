import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext
import webbrowser
import re


# Emoji map
EMOJI_MAP = {
    ":thumbsup:": "👍",
    ":smile:": "😄",
    ":heart:": "❤️",
    ":cry:": "😢",
    ":fire:": "🔥",
    ":laughing:": "😂",
    # Add more as needed
}

"""
    Replaces predefined emoji shortcuts in the message string with actual Unicode emoji.

    Args:
        message (str): The original message containing emoji shortcuts.

    Returns:
        str: Message with emoji shortcuts replaced by emoji characters.
"""

def replace_emoji_shortcuts(message):
    for shortcut, emoji in EMOJI_MAP.items():
        message = message.replace(shortcut, emoji)
    return message

"""
        Initializes the chat client window, prompts for a username,
        sets up GUI components, and starts a thread to receive messages.

        Args:
            master (tk.Tk): The root Tkinter window.
"""
class ChatClient:
    def __init__(self, master):
        self.master = master

        # Prompt for user name
        self.username = simpledialog.askstring("Username", "Please enter your name", parent=self.master)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Setup GUI and connect to server
        self.setup_gui()
        self.connect_to_server()

        # Start background thread to receive messages
        threading.Thread(target=self.receive_messages, daemon=True).start()

    """
        Sets up the GUI layout, including the chat display area,
        input field, and send button. Also binds key events.
    """
    def setup_gui(self):
        # Text area to display messages
        self.text_area = scrolledtext.ScrolledText(self.master, state='disabled', wrap=tk.WORD)
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Entry frame containing input and send button
        self.entry_frame = tk.Frame(self.master)
        self.entry_frame.pack(padx=10, pady=5, fill=tk.X)

        # Entry field for user input
        self.entry_field = tk.Entry(self.entry_frame, font=("Arial", 12))
        self.entry_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry_field.bind("<Return>", self.send_message_event)# Send on Enter
        self.entry_field.bind("<KeyRelease>", self.live_emoji_replace)# Emoji replace on type

        # Send button
        self.send_button = tk.Button(self.entry_frame, text="Send", command=self.send_message_event)
        self.send_button.pack(side=tk.RIGHT)

    """
        Connects to the chat server at localhost on port 5000
        and sends the user's username upon successful connection.

        Also sets the window title to include the username and local port.
    """
    def connect_to_server(self):
        try:
            self.client_socket.connect(("127.0.0.1", 5000))
            self.client_socket.sendall(self.username.encode())
            local_ip, local_port = self.client_socket.getsockname()
            self.master.title(f"Chat Client {self.username} {local_port}")


        except Exception as e:
            print("Connection error:", e)
            self.master.quit()


    """
        Continuously listens for messages from the server and displays them
        in the chat window using the display_message method.
    """
    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                self.display_message(message, "other")
            except Exception as e:
                print("Error receiving message:", e)
                break

    """
        Handles sending a message when the send button is clicked or
        the Enter key is pressed. Replaces emoji shortcuts before sending
        and also displays the message in the chat window.

        Args:
            event: Optional Tkinter event passed from keybinding.
    """
    def send_message_event(self, event=None):
        # Get and sanitize input
        raw_message = self.entry_field.get().strip()
        if not raw_message:
            return
        # Replace emojis and format message
        message = replace_emoji_shortcuts(raw_message)
        full_message = f"{self.username}: {message}"


        try:
            # Send to server and display locally
            self.client_socket.sendall(full_message.encode())
            self.display_message(full_message, "self")
            self.entry_field.delete(0, tk.END)# Clear input field
        except Exception as e:
            print("Error sending message:", e)

    """
        Displays a message in the chat area. Messages from the current
        user are highlighted in light green. URLs are made clickable.

        Args:
            message (str): The message to display.
            msg_type (str): Either "self" for user messages or "other".
    """
    def display_message(self, message, msg_type):
        message = replace_emoji_shortcuts(message)
        self.text_area.configure(state='normal')

        # Record current end index BEFORE inserting message
        start_index = self.text_area.index(tk.END + "-1c")

        # Insert the message
        if msg_type == "self":
            self.text_area.insert(tk.END, message + "\n", "self")
        else:
            self.text_area.insert(tk.END, message + "\n")

        # Make links clickable (pass the full message and start index)
        self.make_links_click(message, start_index)

        self.text_area.configure(state='disabled')
        self.text_area.yview(tk.END)

        # Style self messages
        self.text_area.tag_config("self", background="lightgreen")

    """
        Replaces emoji shortcuts in the message input field in real time
        as the user types.

        Args:
            event: Optional Tkinter event passed from keybinding.
    """
    def live_emoji_replace(self, event=None):
        content = self.entry_field.get()
        new_content = replace_emoji_shortcuts(content)
        if new_content != content:
            pos = self.entry_field.index(tk.INSERT) # Save cursor position
            self.entry_field.delete(0, tk.END)
            self.entry_field.insert(0, new_content)
            self.entry_field.icursor(pos) # Restore cursor position
   
    """
        Finds URLs in a message and makes them clickable in the chat window.

        Args:
            text (str): The message containing potential URLs.
            msg_type (str): Message type (not used, but included for future use).
    """
    def make_links_click(self, text, start_index):
        url_pattern = r'(https?://[^\s]+)'
        urls = list(re.finditer(url_pattern, text))

        for match in urls:
            url = match.group()
            url_start = match.start()
            url_end = match.end()

            # Calculate actual position in the text widget
            line, char = map(int, start_index.split('.'))
            start_idx = f"{line}.{char + url_start}"
            end_idx = f"{line}.{char + url_end}"

            # Create and bind the tag
            self.text_area.tag_add(url, start_idx, end_idx)
            self.text_area.tag_config(url, foreground="blue", underline=True)
            self.text_area.tag_bind(url, "<Button-1>", lambda e, url=url: self.open_link(url))
    """ 
        Opens a given URL in the system's default web browser.

        Args:
            url (str): The URL to open.
    """

    def open_link(self, url):
        # Open the link in the default web browser
        webbrowser.open(url)


if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()




