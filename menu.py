import curses

class Menu:
  def __init__(self, window):
    self.title = "default"
    self.footer = "default"
    self.items = []
    self.window = window
    self.rows, self.cols = self.window.getmaxyx()
    self.index = 0
    self.selected = -1

  def appendItem(self, item):
    self.items.append(item)

  def editItem(self, new, index):
    self.items[index] = new

  def delItem(self, new, index):
    del self.items[index]

  def setFooter(self, footer):
    self.footer = footer

  def setTitle(self, title):
    self.title = title

  def increaseIndex(self):
    self.index = self.index+1
    if self.index == len(self.items):
      self.index = 0

  def decreaseIndex(self):
    self.index = self.index-1
    if self.index < 0:
      self.index = len(self.items)-1
    
  def setSelected(self, index):
    self.selected = index

  def currentItem(self):
    return self.items[self.index]

  def refresh(self):
    #clear window
    self.window.clear()

    #calculate where to place the title
    titleLength = len(self.title)
    x = int(round(self.cols/2) - round(titleLength/2))

    #draw title
    self.window.addstr(0, x, self.title, curses.A_BOLD)

    #draw spacer
    self.window.addstr(1, 0, "═"*self.cols)
  
    #create menu items
    for i in range(0, len(self.items)):
      item = self.items[i]
      if type(item) is dict:
        self.window.addstr(i+2, 0, item["name"])
      else:
        self.window.addstr(i+2, 0, item)
    
    #create text at bottom of screen
    self.window.addstr(self.rows-3, 0, "═"*self.cols)
    self.window.addstr(self.rows-2, 0, self.footer)

    #do highlighting
    for i in range(0, len(self.items)):
      self.window.chgat(i+2, 0, -1, curses.A_NORMAL)
    self.window.chgat(self.index+2, 0, -1, curses.A_REVERSE)
    if self.selected > -1:
      self.window.chgat(self.selected+2, 0, -1, curses.A_UNDERLINE)

    #refresh window
    self.window.refresh()