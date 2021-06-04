import os, random, json, time, threading, curses, traceback

class game:
  def __init__(self):
    #load extradata.json
    f = open("extradata.json")
    self.data = json.load(f)
    f.close()

    #set display size
    self.width = 29
    self.height = 13

    #create blank board to be used internally
    self.blankBoard = []
    for y in range(0, self.height):
      self.blankBoard.append([])
      for x in range(0, self.width):
        self.blankBoard[y].append(0)
    #copies blank board to main board
    self.board = self.blankBoard[:]

    #create displayed board
    self.blankdisplayBoard = []
    for y in range(0, self.height):
      self.blankdisplayBoard.append([])
      for x in range(0, self.width):
        self.blankdisplayBoard[y].append(" ")
    self.displayBoard = self.blankdisplayBoard[:]

    #define variables
    self.length = 1
    self.direction = "east"
    self.previousDirection = "east"
    self.stop = False
    self.resetTimer = False
    self.score = 0
    self.diffuculty = 0
    self.delay = 50

    #set up curses
    self.setupCurses()

    #start main program loop
    self.main()

  #function to set up curses
  def setupCurses(self):
    #configure curses
    self.screen = curses.initscr()
    curses.curs_set(0)
    curses.cbreak()
    curses.noecho()

    #get size of screen
    self.rows, self.cols = self.screen.getmaxyx()
  
  #function to print board
  def printBoard(self):
    #refresh score display
    self.scoreDisplay.addstr(0, 0, "Score: "+str(self.score))
    self.scoreDisplay.refresh()

    #refresh game window
    rows = []
    for y in range(0, self.height):
      rows.append("".join(map(str,self.displayBoard[y])))
    for y in range(0, len(rows)):
      self.gameWindow.addstr(y+1, 1, rows[y])
    self.gameWindow.refresh()
    
  #function to set a pixel on the board
  def setPixel(self, x, y, content):
    self.board[y][x] = content
  
  #function to get the value of a pixel
  def getPixel(self, x, y):
    return self.board[y][x]

  #set the value of a pixel on the screen
  def setDisplayPixel(self, x, y, content):
    self.displayBoard[y][x] = content
  
  #get the value of a pixel on the screen
  def getDisplayPixel(self, x, y):
    return self.displayBoard[y][x]

  #function to generate a food pellet
  def generateFood(self):
    pixels = self.width*self.height
    #gets a random number between 1 and the number of pixels
    #minus the length
    randint = random.randint(1,pixels-self.length)
    counter = 1
    break_ = False
    for y in range(0, self.height):
      for x in range(0, self.width):
        #checks to see if tile is elegible
        if self.board[y][x] == 0:
          #checks to see if the random number == the counter
          if randint == counter:
            #places food if condition is satisfied
            self.setPixel(x, y, -1)
            self.setDisplayPixel(x, y, "$")
            break_ = True
            break
          #increase the counter if condition not satisfied
          counter = counter + 1
      if break_ == True:
        break
    
    #iterate through the board
    for y in range(0, self.height):
      for x in range(0, self.width):
        #if pixel contains a snake piece, increase the time until it despawns
        if self.getPixel(x, y) > 0:
          self.setPixel(x, y, self.getPixel(x, y)+1)
  
  #function to set up game
  def setupGame(self):
    #configure main game window
    self.gameWindow = curses.newwin(self.height+2, self.width+2, 1, 0)
    self.gameWindow.border()

    #configure score display
    self.scoreDisplay = curses.newwin(1, self.width+2, 0, 0)

    #reset some variables
    self.length = 4
    self.board = self.blankBoard[:]
    #sets the location of the head of the snake
    self.head = [int(self.width/2), int(self.height/2)]
    #sets the direction
    self.direction = "east"
    self.previousDirection = "east"
    #generate first food pellet
    self.generateFood()

  #function to handle game tick
  def tick(self):
    #check if direction change is valid, if not then correct it
    if self.direction == self.data["directionalOpposites"][self.previousDirection]:
      self.direction = self.previousDirection[:]

    #places head in new position and check that the head doesnt
    #run into the border
    previousX = self.head[0]
    previousY = self.head[1]
    if self.direction == "east":
      #move self.head
      self.head[0] = self.head[0]+1
      #checks if head is next to wall
      if self.head[0] == self.width:
        #if so, then game over
        return False
    #above comments applicable to code below
    elif self.direction == "west":
      self.head[0] = self.head[0]-1
      if self.head[0] == -1:
        return False
    elif self.direction == "north":
      self.head[1] = self.head[1]-1
      if self.head[1] == -1:
        return False
    else: #note: fallback direction is south
      self.head[1] = self.head[1]+1
      if self.head[1] == self.height:
        return False

    #checks if snake has run into food and update score
    if self.board[self.head[1]][self.head[0]] == -1:
      self.generateFood()
      self.length = self.length + 1
      self.score = self.score + 1

      #calculate diffuculty
      if self.score%5 == 0:
        self.diffuculty = self.diffuculty+1
        #change amount of delay depending on diffuculty
        self.delay = int(50*(0.75**self.diffuculty))
    
    #iterates through board and decreases the ticks remaining
    #for each part of the snake
    for y in range(0, self.height):
      for x in range(0, self.width):
        if self.getPixel(x, y) > 0:
          #updates the value of the snake piece
          self.setPixel(x, y, self.getPixel(x, y)-1)
          #clears a pixel on the display
          if self.getPixel(x, y) == 0:
            self.setDisplayPixel(x, y, " ")
    
    #checks to see if snake has run into itself
    if self.board[self.head[1]][self.head[0]] > 0:
      return False
    
    #updates location of head internally
    self.setPixel(self.head[0], self.head[1], self.length)

    newX = self.head[0]
    newY = self.head[1]
    #updates location of head on display, using direction to determine
    #the ascii character used
    #check if snake is going horizontally
    if self.direction in self.data["horizontalDirections"]:
      #set the head on the display to the correct character
      self.setDisplayPixel(newX, newY, self.data["displayCharactersASCII"]["horizontal"])
    else: #if not then the snake is going vertially
      self.setDisplayPixel(newX, newY, self.data["displayCharactersASCII"]["vertical"])

    #check if snake has turned
    if not self.direction == self.previousDirection:
      #uhhh idk why this works but it does
      if sorted([self.direction, self.data["directionalOpposites"][self.previousDirection]]) == sorted(self.data["north-west"]):
        self.setDisplayPixel(previousX, previousY, self.data["displayCharactersASCII"]["north-west"])
      #basically the same code as above
      elif sorted([self.direction, self.data["directionalOpposites"][self.previousDirection]]) == sorted(self.data["south-west"]):
        self.setDisplayPixel(previousX, previousY, self.data["displayCharactersASCII"]["south-west"])

      elif sorted([self.direction, self.data["directionalOpposites"][self.previousDirection]]) == sorted(self.data["north-east"]):
        self.setDisplayPixel(previousX, previousY, self.data["displayCharactersASCII"]["north-east"])

      elif sorted([self.direction, self.data["directionalOpposites"][self.previousDirection]]) == sorted(self.data["south-east"]):
        self.setDisplayPixel(previousX, previousY, self.data["displayCharactersASCII"]["south-east"])
        
      else: #fall back to using #
        self.setDisplayPixel(previousX, previousY, "#")

    #return True if tick successful
    self.previousDirection = self.direction[:]
    return True
  
  def gameOverHandler(self):
    #calculate where to place window
    #size = self.gameWindow.getmaxyx()
    text = "GAME OVER"
    windowHeight = 3
    y = int(round(self.rows/2 - (len(text)+2)/2))
    x = int(round(self.rows/2 - windowHeight/2))

    #display a window saying GAME OVER
    self.gameOverWindow = curses.newwin(windowHeight, len(text)+2, y, x)
    self.gameOverWindow.border()
    self.gameOverWindow.addstr(1, 1, "GAME OVER")
    self.gameOverWindow.refresh()

  def mainMenuHandler(self):
    #calculate where to place the title
    titleLength = len(max(self.data["titleText"], key=len))
    x = int(round(self.cols/2) - round(titleLength/2))

    #create window for title
    self.titleWindow = curses.newwin(7, titleLength+1, 0, x)
    
    #add text to window
    for i in range(0, len(self.data["titleText"])):
      self.titleWindow.addstr(i, 0, self.data["titleText"][i])
    
    #create window displaying main menu text
    self.mainMenuWindow = curses.newwin(self.rows, self.cols, 8, 0)

    #calculate where to place text
    text = self.data["mainMenuText"]
    textStart = int(round(self.cols/2) - round(len(text)/2))
    self.mainMenuWindow.addstr(0, textStart, text)

    #refresh windows
    self.titleWindow.refresh()
    self.mainMenuWindow.refresh()

    #wait until keypress to continue
    self.mainMenuWindow.getkey()

  def updateGame(self):
    while True:
      #idk how to do fancy stuff with threading, this works anyways
      #basically it sleeps for half a second and checks if the timer
      #has to be reset due to an input
      for i in range(0, self.delay):
        time.sleep(0.01)
        if self.resetTimer == True:
          break
      if self.resetTimer == True:
        self.resetTimer = False
        continue

      #stop if this condition is met
      if self.stop == True:
        break

      #run a tick and stop if game over
      if self.tick() == False:
        self.stop = True
        break

      #refresh the board
      self.printBoard()
        
  #main program function
  def main(self):
    #show main menu screen
    self.mainMenuHandler()

    #set up game
    self.setupGame()
    self.previousDirection = "east"

    #start thread
    self.thread = threading.Thread(target=self.updateGame)
    self.thread.start()

    #start main program loop
    while True:
      #get keyboard input
      key = self.screen.getkey()
      if self.stop == True:
        break

      #process keyboard input
      #if input is valid then run a tick
      if key in self.data["directionalControls"]:
        self.direction = self.data["directionalControls"][key]
        #if player loses, break from loop
        if self.tick() == False:
          self.stop = True
        else: #if not then refresh board
          self.printBoard()
          #reset the timer of the other thread
          self.resetTimer = True
          
      #break if key x is pressed
      elif key == "x":
        self.stop = True
      if self.stop == True:
        break

    #display game over screen
    self.gameOverHandler()
    curses.napms(1000)

    #program will terminate after any key pressed
    self.screen.getkey()

#run the game if this is the main thread
if __name__ == "__main__":
  try:
    game()
    #when game ends quit curses
    curses.endwin()
  
  #quit curses and print exception if there was an error
  except Exception: 
    curses.endwin()
    traceback.print_exc()  