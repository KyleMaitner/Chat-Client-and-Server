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


def replace_emoji_shortcuts(message):
    for shortcut, emoji in EMOJI_MAP.items():
        message = message.replace(shortcut, emoji)
    return message


class ChatClient:
    def __init__(self, master):
        self.master = master


        self.username = simpledialog.askstring("Username", "Please enter your name", parent=self.master)


        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


        self.setup_gui()
        self.connect_to_server()


        threading.Thread(target=self.receive_messages, daemon=True).start()


    def setup_gui(self):
        self.text_area = scrolledtext.ScrolledText(self.master, state='disabled', wrap=tk.WORD)
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)


        self.entry_frame = tk.Frame(self.master)
        self.entry_frame.pack(padx=10, pady=5, fill=tk.X)


        self.entry_field = tk.Entry(self.entry_frame, font=("Arial", 12))
        self.entry_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry_field.bind("<Return>", self.send_message_event)
        self.entry_field.bind("<KeyRelease>", self.live_emoji_replace)


        self.send_button = tk.Button(self.entry_frame, text="Send", command=self.send_message_event)
        self.send_button.pack(side=tk.RIGHT)


    def connect_to_server(self):
        try:
            self.client_socket.connect(("127.0.0.1", 5000))
            self.client_socket.sendall(self.username.encode())
            local_ip, local_port = self.client_socket.getsockname()
            self.master.title(f"Chat Client {self.username} {local_port}")


        except Exception as e:
            print("Connection error:", e)
            self.master.quit()


    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                self.display_message(message, "other")
            except Exception as e:
                print("Error receiving message:", e)
                break


    def send_message_event(self, event=None):
        raw_message = self.entry_field.get().strip()
        if not raw_message:
            return
        message = replace_emoji_shortcuts(raw_message)
        full_message = f"{self.username}: {message}"


        try:
            self.client_socket.sendall(full_message.encode())
            self.display_message(full_message, "self")
            self.entry_field.delete(0, tk.END)
        except Exception as e:
            print("Error sending message:", e)


    def display_message(self, message, msg_type):
        #apply emoji replacements before displaying
        message = replace_emoji_shortcuts(message)


        self.text_area.configure(state='normal')
        if msg_type == "self":
            self.text_area.insert(tk.END, message + "\n", "self")
        else:
            self.text_area.insert(tk.END, message + "\n")
       
        #Make links clickable
        self.make_links_click(message, msg_type)


        self.text_area.configure(state='disabled')
        self.text_area.yview(tk.END)


        # Style
        self.text_area.tag_config("self", background="lightgreen")


    def live_emoji_replace(self, event=None):
        content = self.entry_field.get()
        new_content = replace_emoji_shortcuts(content)
        if new_content != content:
            pos = self.entry_field.index(tk.INSERT)
            self.entry_field.delete(0, tk.END)
            self.entry_field.insert(0, new_content)
            self.entry_field.icursor(pos)
   
    def make_links_click(self, text, msg_type):
        # Regular expression to detect URLs
        url_pattern = r'(https?://[^\s]+)'


        # Find all URLs in the provided text
        urls = re.findall(url_pattern, text)


        # Apply clickable links for each URL
        for url in urls:
            start_idx = text.find(url)
            end_idx = start_idx + len(url)


            # Add tag to the URL part of the text
            self.text_area.tag_add(url, f"1.{start_idx}", f"1.{end_idx}")
            self.text_area.tag_config(url, foreground="blue", underline=True)


            # Bind the URL to the open_link function
            self.text_area.tag_bind(url, "<Button-1>", lambda e, url=url: self.open_link(url))
           


    def open_link(self, url):
        # Open the link in the default web browser
        webbrowser.open(url)






if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()





