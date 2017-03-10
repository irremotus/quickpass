#!/usr/bin/python
"""Pass GUI App"""

import os
from os.path import expanduser
import subprocess
import tkinter
import tkinter.font as tkFont

import gnupg


def clipboard_copy(text):
    """Copy text to the clipboard."""
    result = subprocess.run(
        # "primary" because "clipboard" doesn't seem to work for all apps
        # you must paste with middle click
        ["xclip", "-selection", "primary", "-l", "1"],
        input=bytes(text, encoding="utf-8")
        )
    if result.returncode == 0:
        print("Copied:", text)
    else:
        print("Error copying")


class ListItem:
    """A file in a listbox."""
    def __init__(self, parent, itemname="", itempath="", basepath=""):
        self.itemname = itemname[:-4]
        self.itempath = itempath
        self.fullpath = basepath + itempath
        self.parent = parent
        self.indent = parent.indent + 1
        self.used = False

    def __str__(self):
        return "    " * self.indent + self.itemname


class ListDir:
    """A directory in a listbox."""
    def __init__(self, parent=None, itemname="", itempath="", basepath="", contents=None):
        self.itemname = itemname
        self.itempath = itempath
        self.fullpath = basepath + itempath
        if parent:
            self.indent = parent.indent + 1
        else:
            self.indent = -1
        if contents:
            self.contents = contents
        else:
            self.contents = []
        self.used = False

    def __str__(self):
        return "    " * self.indent + self.itemname + "/"


def get_dir_list(basepath):
    """Create a recursive list of directories and files."""
    parent = ListDir(basepath=basepath)
    parent.contents = get_dir_list_recurse(basepath, parent=parent)
    return parent


def get_dir_list_recurse(basepath, itempath="", parent=None):
    """Walk directory tree for get_dir_list."""
    total = []
    if not basepath.endswith("/"):
        basepath = basepath + "/"
    if itempath and not itempath.endswith("/"):
        itempath = itempath + "/"
    items = os.listdir(basepath + itempath)
    for itemname in items:
        curpath = basepath + itempath + itemname
        if os.path.isdir(curpath):
            dirobj = ListDir(
                basepath=basepath,
                itempath=itempath + itemname,
                itemname=itemname,
                parent=parent
            )
            dirobj.contents = get_dir_list_recurse(
                basepath,
                itempath=itempath+itemname,
                parent=dirobj
            )
            total.append(dirobj)
        else:
            fileobj = ListItem(
                parent,
                basepath=basepath,
                itempath=itempath + itemname,
                itemname=itemname
            )
            total.append(fileobj)
    return total


def format_dir_list(curdir, search=""):
    """Format the list of directories."""
    dir_list = format_dir_list_recurse(curdir, search=search)
    return dir_list[::-1]


def format_dir_list_recurse(curdir, search=""):
    """Format the list of directories."""
    total = []
    for item in curdir.contents:
        if isinstance(item, ListDir):
            total.extend(format_dir_list_recurse(item, search=search))
            if item.used:
                total.append(item)
        elif isinstance(item, ListItem):
            if search in item.itempath:
                item.used = True
                curdir.used = True
                total.append(item)
    return total


class PassGUI(tkinter.Tk):
    """ Get a string from the user """
    def __init__(self, parent=None):
        tkinter.Tk.__init__(self, parent)
        self.parent = parent
        self.homedir = expanduser("~") + "/"
        self.passdir = self.homedir + ".password-store-personal"
        self.initialize()
        self.update_list()
        self.mainloop()

    def initialize(self):
        """ initialize """
        # scale up for 4k display
        self.tk.call('tk', 'scaling', 4.0)
        self.custom_font = tkFont.Font(family="Helvetica", size=12)
        # keep this window on top
        #self.wm_attributes('-topmost', 1)
        # make the window maximized
        win_width = self.winfo_screenwidth() // 4
        win_height = self.winfo_screenheight() // 2
        # center the window on the screen
        self.eval('tk::PlaceWindow %s center' % self.winfo_pathname(self.winfo_id()))
        geo = [int(x) for x in self.geometry().replace("x", " ").replace("+", " ").split()]
        geo[0] = win_width
        geo[1] = win_height
        geo[2] -= win_width // 2
        geo[3] -= win_height // 2
        self.geometry("{geo[0]}x{geo[1]}+{geo[2]}+{geo[3]}".format(geo=geo))
        # set the layout manager
        self.grid()
        self.bind("<Escape>", self.on_press_escape)
        self.title("QuickPass")

        # Name entry box
        self.entry_var = tkinter.StringVar()
        self.entry = tkinter.Entry(self, textvariable=self.entry_var, font=self.custom_font)
        self.entry.grid(row=1, column=0, sticky="EW")
        self.entry.bind("<KeyRelease>", self.on_key_press)
        self.entry.bind("<Return>", self.on_press_enter)
        self.entry_var.set("")

        # Name label
        self.label_var = tkinter.StringVar()
        self.label = tkinter.Label(
            self,
            textvariable=self.label_var,
            anchor="w",
            fg="black",
            bg="gray",
            font=self.custom_font
        )
        self.label.grid(row=0, column=0, columnspan=1, sticky="EW")
        self.label_var.set("Search items")

        # List of items
        self.list = tkinter.Listbox(self, font=self.custom_font, exportselection=False)
        self.list.grid(row=2, column=0, sticky="NESW")
        self.list.bind("<Double-1>", self.on_double_click)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        #self.resizable(True, False)
        self.entry.focus_set()
        self.entry.selection_range(0, tkinter.END)

    def update_list(self, name=""):
        """Delete all the items in the list, and add new ones."""
        self.list.delete(0, tkinter.END)
        items = format_dir_list(get_dir_list(self.passdir), search=name)
        self.curlistitems = items
        for item in items:
            self.list.insert(tkinter.END, str(item))
        # find the first file, and set selection to it
        index = 0
        for index, item in enumerate(items):
            if isinstance(item, ListItem):
                break
        self.list.selection_set(index)

    def on_key_press(self, event):
        """Perform these actions every time a key is pressed."""
        del event
        name = self.entry_var.get()
        self.update_list(name=name)
    
    def on_double_click(self, event):
        """Check the type of item being clicked; if it's a file, execute <Return>"""
        del event
        index = self.list.curselection()
        item = self.curlistitems[index[0]]
        print("double click")
        if isinstance(item, ListItem):
            print("file")
            self.on_press_enter(None)
        else:
            print("folder")

    def on_press_enter(self, event):
        """ copy the selected password when enter is pressed """
        del event
        print("enter")
        index = self.list.curselection()
        item = self.curlistitems[index[0]]
        self.set_label("Waiting for decryption...", "yellow")
        try:
            password = self.get_pass(item)
        except self.DecryptionFailedException as error:
            self.unset_label()
            self.flash_label(error.message, "red", 2000)
        else:
            self.unset_label()
            clipboard_copy(password)
            self.destroy()

    def flash_label(self, message, color, time):
        """Show a colored message for a period of time"""
        self.set_label(message, color)
        self.after(time, self.unset_label)

    def set_label(self, message, color):
        """Set the label message and color"""
        self.label.prev_str = self.label_var.get()
        self.label.prev_color = self.label.configure()["background"][4]
        self.label_var.set(message)
        self.label.configure(bg=color)
        self.update()
        print("set color")

    def unset_label(self):
        """Set the label to its previous value"""
        self.set_label(self.label.prev_str, self.label.prev_color)
        print("unset color")

    def on_press_escape(self, event):
        """Close out the program."""
        del event
        self.destroy()

    def get_contents(self, item):
        """ get the contents of an encrypted file by name """
        return self.decrypt(item.fullpath)

    class DecryptionFailedException(Exception):
        """Decryption Failed"""
        def __init__(self, message):
            super().__init__()
            self.message = message

    def decrypt(self, path):
        """ decrypt the file at path """
        with open(path, "rb") as fileh:
            gpg = gnupg.GPG(gnupghome=self.homedir+".gnupg")
            decrypted = gpg.decrypt_file(fileh)
            if decrypted.ok:
                return str(decrypted)
            else:
                raise self.DecryptionFailedException(decrypted.status)

    def get_pass(self, item):
        """ get the password by name """
        text = self.get_contents(item)
        lines = text.split("\n")
        password = lines[0]
        return password



if __name__ == "__main__":
    PassGUI()
    #x = get_dir_list("/home/kschmittle/.password-store-personal/")
    #f = format_dir_list(x, search="")
    #for item in f:
    #    print(item)
