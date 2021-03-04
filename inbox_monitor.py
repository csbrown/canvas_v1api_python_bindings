import time
import tkinter as tk
from canvas_api import *
import subprocess

def ontopper(window_title):
    time.sleep(1)
    ONTOPPER = 'wmctrl -r "{}" -b add,above'.format(window_title)
    subprocess.run(ONTOPPER, shell=True)
    
def popupmsg(msg):
    WINDOW_TITLE = "check a thing!"
    popup = tk.Tk()
    popup.wm_title(WINDOW_TITLE)
    label = tk.Label(popup, text=msg)
    label.pack(side="top", fill="x", pady=10)
    B1 = tk.Button(popup, text="Okay", command = popup.destroy)
    B1.pack()
    popup.bind("<FocusIn>", lambda event: ontopper(WINDOW_TITLE))
    popup.mainloop()

def monitor_inbox():
    conversations_api = ConversationsAPI(TOKEN)
    previous_inbox_value = conversations_api.get_unread_count()
    while True:
        time.sleep(1)
        new_inbox_value = conversations_api.get_unread_count()
        if previous_inbox_value < new_inbox_value:
            popupmsg("you've got canvas mail!")

if __name__ == "__main__":
    monitor_inbox()
