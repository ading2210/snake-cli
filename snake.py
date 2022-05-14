import os, random, json, time, threading, curses, traceback, menu, hashlib, copy

class Game:
  def __init__(self):
    #load extradata.json
    f = open("extradata.json", encoding="utf-8")
    self.data = json.load(f)
    f.close()

    self.options = {}

    #read default values for variables
    self.defaultOptions = {}
    for item in self.data["optionsMenuItems"]:
      if item["save"] == True:
        self.defaultOptions[item["id"]] = item["default"]

    #read options.json
    self.basePath = os.path.abspath(os.path.dirname(__file__))
    if os.path.exists(self.basePath+"/options.json"):
      self.loadOptions()
    else:
      self.saveOptions(options=self.defaultOptions)
      self.options = dict(self.defaultOptions)

    #set display size
    self.width = 17
    self.height = 13

    #set up curses
    self.setupCurses()

    #ansi escape codes to hightlight stuff
    self.hightlight = "\033[7m"
    self.reset = "\033[0m"
    
    self.resetGame()

  def resetGame(self):
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
      for x in range(0, self.width*2):
        self.blankdisplayBoard[y].append(" ")
    self.displayBoard = self.blankdisplayBoard[:]

    #define variables
    self.length = 1
    self.direction = "east"
    self.previousDirection = "east"
    self.stop = False
    self.resetTimer = False
    self.score = 0
    self.delay = 50
    self.extra_turn = False
    self.extra_turn_active = False
    self.inputQueue = []
    self.currentHighScore = 0
    self.play_sound = False

    self.applyOptions()


  def applyOptions(self):
    if self.options["speed"] == "Normal":
      self.delay = 25
    elif self.options["speed"] == "Fast":
      self.delay = 15
    elif self.options["speed"] == "Slow":
      self.delay = 40
    if self.options["extra_turn"] == "True":
      self.extra_turn = True
      self.extra_turn_active = False
    if self.options["play_sound"] == "True":
      self.playSound = True

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
    scoreText = "Score: {score} | Best: {highScore}".format(
      score=str(self.score), highScore=self.currentHighScore)
    self.scoreDisplay.addstr(0, 0, scoreText)
    self.scoreDisplay.refresh()

    #refresh game window
    rows = []
    for y in range(0, self.height):
      rows.append("".join(map(str,self.displayBoard[y])))
    for y in range(0, len(rows)):
      self.gameWindow.addstr(y+1, 1, rows[y])
    self.gameWindow.border()
    self.gameWindow.refresh()

  #function to set a pixel on the board
  def setPixel(self, x, y, content):
    self.board[y][x] = content

  #function to get the value of a pixel
  def getPixel(self, x, y):
    return self.board[y][x]

  #set the value of a pixel on the screen
  def setDisplayPixel(self, x, y, content):
    self.displayBoard[y][x*2] = content
  def setDisplayPixelNoScaling(self, x, y, content):
    self.displayBoard[y][x] = content

  #get the value of a pixel on the screen
  def getDisplayPixel(self, x, y):
    return self.displayBoard[y][x]

  #function to generate a food pellet
  def generateFood(self):
    eligible_tiles = []
    for y in range(0, self.height):
      for x in range(0, self.width):
        #checks to see if tile is eligible
        if self.board[y][x] == 0:
          #if so, then the tile is appended to a list of eligible tiles
          eligible_tiles.append((y,x))

    if len(eligible_tiles) > 0:
      #one tile is chosen and the food is placed
      y, x = random.choice(eligible_tiles)
      self.setPixel(x, y, -1)
      self.setDisplayPixel(x, y, "$")

  #this function generates a barrier, which is basically
  #the same as the previous function
  def generateBarrier(self):
    eligible_tiles = []
    for y in range(0, self.height):
      for x in range(0, self.width):
        #checks to see if tile is eligible
        tiles = ((y+1,x),(y-1,x),(y,x+1),(y,x-1),(y,x),
                 (y+1,x-1),(y+1,x+1),(y-1,x-1),(y-1,x+1))
        counter = 0
        #checks every adjacent tile to see if it is occupied
        for tile in tiles:
          if tile[0] >= self.height or tile[0] < 0:
            break
          elif tile[1] >= self.width or tile[1] < 0:
            break
          if self.board[tile[0]][tile[1]] != 0:
            break
          counter += 1
        #if all adjacent tiles are empty, the tile is appended
        #to a list of eligible tiles
        if counter == 9:
          eligible_tiles.append((y,x))

    if len(eligible_tiles) > 0:
      #one tile is chosen and the barrier is placed
      y, x = random.choice(eligible_tiles)
      self.setPixel(x, y, -2)
      self.setDisplayPixel(x, y, self.data["displayCharactersASCII"]["barrier"])
      self.setDisplayPixelNoScaling(x*2-1, y, self.data["displayCharactersASCII"]["barrier"])

  #function to set up game
  def setupGame(self):
    #load the previous high score
    self.currentHighScore = self.loadHighScore()
    self.oldHighScore = self.currentHighScore
    
    #calculate where to place main window
    windowWidth = self.width*2 + 1
    self.windowStart = int(round(self.cols/2) - round(windowWidth/2))

    #configure main game window
    self.gameWindow = curses.newwin(self.height+2, windowWidth, 1, self.windowStart)
    self.gameWindow.border()

    #configure score display
    self.scoreDisplay = curses.newwin(1, self.width*2+2, 0, self.windowStart)

    #reset some variables
    self.length = 4
    self.score = 0
    self.board = self.blankBoard[:]
    self.displayBoard = self.blankdisplayBoard[:]

    #sets the location of the head of the snake
    self.head = [int(self.width/2), int(self.height/2)]

    #sets the direction
    self.direction = "east"
    self.previousDirection = "east"

    #generate first food pellet
    self.generateFood()

    #set game window to nodelay mode
    self.gameWindow.nodelay(True)

  #function to handle game tick
  def tick(self):
    #check if direction change is valid, if not then correct it
    if self.direction == self.data["directionalOpposites"][self.previousDirection]:
      self.direction = self.previousDirection[:]

    #places head in new position and check that the head doesnt
    #run into the border
    previousX = self.head[0]
    previousY = self.head[1]
    newHead = self.head[:]
    if self.direction == "east":
      #move self.head
      newHead[0] = self.head[0]+1
      #checks if head is next to wall
      if newHead[0] >= self.width:
        #if so, then game over
        return False
    #above comments applicable to code below
    elif self.direction == "west":
      newHead[0] = self.head[0]-1
      if newHead[0] <= -1:
        return False
    elif self.direction == "north":
      newHead[1] = self.head[1]-1
      if newHead[1] <= -1:
        return False
    else: #note: fallback direction is south
      newHead[1] = self.head[1]+1
      if newHead[1] >= self.height:
        return False
    #checks if snake has run into a barrier
    if self.board[newHead[1]][newHead[0]] == -2:
      return False

    #checks to see if snake has run into itself
    if self.board[newHead[1]][newHead[0]] > 0:
      return False

    self.head = newHead[:]

    #checks if snake has run into food and update score
    if self.board[self.head[1]][self.head[0]] == -1:
      self.generateFood()
      self.length += 1
      self.score += 1
      if self.playSound == True:
        curses.beep()
      if self.score > self.currentHighScore:
        self.currentHighScore = self.score
      #iterate through the board
      for y in range(0, self.height):
        for x in range(0, self.width):
          #if pixel contains a snake piece, increase the time until it despawns
          if self.getPixel(x, y) > 0:
            self.setPixel(x, y, self.getPixel(x, y)+1)

      #place a barrier every other point
      if self.options["create_barriers"] == "True":
        if self.score%2 == 0:
          self.generateBarrier()

      #increase diffuculty, ignore if disabled
      if self.options["increase_difficulty"] == "True":
        if self.score%5 == 0:
          #change amount of delay depending on diffuculty
          self.delay = int(self.delay*0.95)

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
            #fix this later plz
            self.setDisplayPixelNoScaling(x*2-1, y, " ")
            
    #display food
    for y in range(0, self.height):
      for x in range(0, self.width):
        if self.getPixel(x, y) == -1:
          self.setDisplayPixel(x, y, "$")

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
      if self.direction != "west" or self.direction == self.previousDirection:
        self.setDisplayPixelNoScaling(newX*2-1, newY, self.data["displayCharactersASCII"]["horizontal"])
      if self.direction != "west" and self.direction == self.previousDirection:
        self.setDisplayPixelNoScaling(newX*2-1, newY, self.data["displayCharactersASCII"]["horizontal"])
      elif self.direction == "west" and self.direction == self.previousDirection:
        self.setDisplayPixelNoScaling(newX*2+1, newY, self.data["displayCharactersASCII"]["horizontal"])
    else: #if not then the snake is going vertially
      self.setDisplayPixel(newX, newY, self.data["displayCharactersASCII"]["vertical"])

    #check if snake has turned
    if not self.direction == self.previousDirection:
      if self.direction == "west" and self.previousDirection in self.data["verticalDirections"]:
        self.setDisplayPixelNoScaling(previousX*2-1, previousY, self.data["displayCharactersASCII"]["horizontal"])
      #uhhh idk why this works but it does
      if sorted([self.direction, self.data["directionalOpposites"][self.previousDirection]]) == sorted(self.data["north-west"]):
        self.setDisplayPixel(previousX, previousY, self.data["displayCharactersASCII"]["north-west"])
      #basically the same code as above
      elif sorted([self.direction, self.data["directionalOpposites"][self.previousDirection]]) == sorted(self.data["south-west"]):
        self.setDisplayPixel(previousX, previousY, self.data["displayCharactersASCII"]["south-west"])

      elif sorted([self.direction, self.data["directionalOpposites"][self.previousDirection]]) == sorted(self.data["north-east"]):
        self.setDisplayPixel(previousX, previousY, self.data["displayCharactersASCII"]["north-east"])
        self.setDisplayPixelNoScaling(previousX*2-1, previousY, " ")

      elif sorted([self.direction, self.data["directionalOpposites"][self.previousDirection]]) == sorted(self.data["south-east"]):
        self.setDisplayPixel(previousX, previousY, self.data["displayCharactersASCII"]["south-east"])
        self.setDisplayPixelNoScaling(previousX*2-1, previousY, " ")

      else: #fall back to using #
        self.setDisplayPixel(previousX, previousY, "#")

    #return True if tick successful
    self.previousDirection = self.direction[:]
    return True

  def gameOverHandler(self):
    #save the new high score if it is higher than the old one
    if self.score > self.oldHighScore:
      self.saveHighScore(self.score)
    
    #turn off nodelay mode for game window
    self.gameWindow.nodelay(False)

    #calculate where to place window
    windowHeight = 4
    windowWidth = 20
    y = int(round((self.height+2)/2 - windowHeight/2))
    x = int(round((self.width*2+2)/2 - (windowWidth)/2)) + self.windowStart

    #display a window saying GAME OVER
    self.gameOverWindow = curses.newwin(windowHeight, windowWidth, y, x)
    self.gameOverWindow.border()
    self.gameOverWindow.addstr(1, 1, "    GAME OVER    ")
    self.gameOverWindow.addstr(2, 1, "Play Again? [Y/N]")
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
    self.mainMenuWindow = curses.newwin(self.rows-8, self.cols, 8, 0)
    self.mainMenuWindow2 = curses.newwin(self.rows-9, self.cols, 9, 0)

    #calculate where to place text
    text = self.data["mainMenuText"]
    text2 = self.data["mainMenuText2"]
    textStart = int(round(self.cols/2) - round(len(text)/2))
    textStart2 = int(round(self.cols/2) - round(len(text2)/2))
    self.mainMenuWindow.addstr(0, textStart, text)
    self.mainMenuWindow2.addstr(0, textStart2, text2)

    #refresh windows
    self.titleWindow.refresh()
    self.mainMenuWindow.refresh()
    self.mainMenuWindow2.refresh()

    #wait until keypress to continue
    key = self.mainMenuWindow.getkey()

    #hide windows
    self.titleWindow.clear()
    self.mainMenuWindow.clear()
    self.mainMenuWindow2.clear()
    self.titleWindow.refresh()
    self.mainMenuWindow.refresh()
    self.mainMenuWindow2.refresh()

    return key

  def optionsScreen(self):
    items = self.data["optionsMenuItems"]
    #create window for menu
    self.optionsMenuWindow = curses.newwin(self.rows, self.cols, 0, 0)
    self.optionsMenuWindow.keypad(1)
    self.optionsMenu = menu.Menu(self.optionsMenuWindow)

    #set up options menu
    self.optionsMenu.setTitle("Configure game:")
    self.optionsMenu.setFooter("Use arrow keys to navigate. Enter to select. X to exit.")

    #set items
    for item in items:
      if item["type"] == "line":
        item = "─"*self.cols
        self.optionsMenu.appendItem(item)
        continue
      newitem = copy.copy(item)
      if item["type"] != "text":
        newitem["oldName"] = newitem["name"]
        newitem["name"] = newitem["name"]+" ({value})".format(value=self.options[newitem["id"]])
      self.optionsMenu.appendItem(newitem)
    self.optionsMenu.appendItem("─"*self.cols)
    self.optionsMenu.appendItem("Reset to default")
    self.optionsMenu.appendItem("Reset high scores")
    self.optionsMenu.appendItem("Save and exit")
    self.optionsMenu.refresh()

    #loop to handle inputs
    while True:
      key = self.optionsMenuWindow.getch()

      if key == ord("x"):
        break
      elif key == curses.KEY_UP: #up
        self.optionsMenu.decreaseIndex()
        if self.optionsMenu.currentItemText() == "─"*self.cols:
          self.optionsMenu.decreaseIndex()
      elif key == curses.KEY_DOWN: #down
        self.optionsMenu.increaseIndex()
        if self.optionsMenu.currentItemText() == "─"*self.cols:
          self.optionsMenu.increaseIndex()

      elif key == 10 or key == 13: #enter
        item = self.optionsMenu.items[self.optionsMenu.index]
        
        if item == "Reset high scores":
          if os.path.exists(self.basePath+"/scores.json"):
             os.remove(self.basePath+"/scores.json")
          item = {
            "name": "Reset high scores",
            "id": "popup",
            "type": "text",
            "default": ["The saved high scores have been cleared."],
            "oldName": "Reset high scores"
          }
        if item == "Save and exit":
          break
        elif item == "Reset to default":
          self.saveOptions(options=self.defaultOptions)
          self.options = dict(self.defaultOptions)
        elif item == "─"*self.cols:
          continue
        else:
          #raise Exception(item)
          #create submenu
          submenuWindow = curses.newwin(self.rows, self.cols, 0, 0)
          submenuWindow.keypad(1)
          submenu = menu.Menu(submenuWindow)
          submenu.setTitle("Submenu: "+item["name"])
          submenu.setFooter("Use arrow keys to navigate. Enter to select. X to exit.")

          #create items in submenu
          if item["type"] == "toggle":
            submenu.items = ["True", "False", "─"*self.cols] + ["<- Back"]
          elif item["type"] == "choice":
            submenu.items = item["choices"] + ["─"*self.cols] + ["<- Back"]
            
          elif item["type"] == "text":
            submenu.items = item["default"]
            submenu.items = submenu.items + ["─"*self.cols] + ["<- Back"]

          #hide main options menu
          self.optionsMenuWindow.clear()
          self.optionsMenuWindow.refresh()

          #show submenu
          if item["type"] == "text":
            submenu.decreaseIndex()
          submenu.refresh()

          #main loop for submenu
          while True:
            #get key
            key = submenuWindow.getch()

            #if x is pressed then exit menu
            if key == ord("x"):
              break
            if item["type"] != "text":
              if key == curses.KEY_UP: #up
                submenu.decreaseIndex()
                if submenu.currentItem() == "─"*self.cols:
                  submenu.decreaseIndex()
              if key == curses.KEY_DOWN: #down
                submenu.increaseIndex()
                if submenu.currentItem() == "─"*self.cols:
                  submenu.increaseIndex()

            #this is run when the enter key is pressed
            if key == 10 or key == 13:
              currentItem = submenu.currentItem()

              #check the type of the item
              #if it is a string, then proceed
              #break if back is selected
              if currentItem == "<- Back":
                break
              else:
                optionsMenuItems = self.data["optionsMenuItems"]
                #change the appropriate value in the options
                for menuItem in optionsMenuItems:
                  if menuItem["id"] == item["id"]:
                    self.options[menuItem["id"]] = currentItem
                    break
              if type(currentItem) is dict:
                pass
              break
            submenu.refresh()
        
        #update menu with new options
        counter = 0
        for item in self.optionsMenu.items:
          if type(item) is dict:
            if item == "Save and exit.":
              continue
            elif item == "Reset to default":
              continue
            if item["type"] != "text":
              item["name"] = item["oldName"]+" ({value})".format(value=self.options[item["id"]])
            self.optionsMenu.editItem(item, counter)
          counter = counter+1
      else:
        continue

      #refresh
      self.optionsMenu.refresh()

    #apply new options when done
    self.saveOptions()
    self.applyOptions()

    #hide windows
    self.optionsMenuWindow.clear()
    self.optionsMenuWindow.refresh()

  def saveOptions(self, options=None):
    if options == None:
      options = self.options
        
    with open(self.basePath+"/options.json", "w") as outfile:
      json.dump(options, outfile, indent=2)

  def loadOptions(self):
    optionsFile = open(self.basePath+"/options.json")
    self.options = json.load(optionsFile)
    optionsFile.close()

    for option in self.data["optionsMenuItems"]:
      if not option["id"] in self.options and option["save"] == True:
        self.options[option["id"]] = option["default"]

  def saveHighScore(self, score):
    #read the options file and get the hash
    optionsFile = open(self.basePath+"/options.json")
    optionsString = optionsFile.read()
    optionsStringEncoded = optionsString.encode("utf-8")
    optionsFile.close()
    optionsHash = hashlib.sha1(optionsStringEncoded).hexdigest()

    #read the scores.json file if it exists
    if os.path.exists(self.basePath+"/scores.json"):
      scoresFile = open(self.basePath+"/scores.json")
      scoresString = scoresFile.read()
      scoresFile.close()
      scores = json.loads(scoresString)
    else:
      scores = {}

    #write the new score
    scores[optionsHash] = score
    with open(self.basePath+"/scores.json", "w") as outfile:
      json.dump(scores, outfile, indent=2)

  def loadHighScore(self):
    #read the options file and get the hash
    optionsFile = open(self.basePath+"/options.json")
    optionsString = optionsFile.read()
    optionsStringEncoded = optionsString.encode("utf-8")
    optionsFile.close()
    optionsHash = hashlib.sha1(optionsStringEncoded).hexdigest()

    #read the scores.json file if it exists
    if os.path.exists(self.basePath+"/scores.json"):
      scoresFile = open(self.basePath+"/scores.json")
      scoresString = scoresFile.read()
      scoresFile.close()
      scores = json.loads(scoresString)
    else:
      #create it if it does not exist
      scores = {}
      with open(self.basePath+"/scores.json", "w") as outfile:
        json.dump(scores, outfile, indent=2)

    #return the score
    if optionsHash in scores:
      return scores[optionsHash]
    else:
      return 0

  def getInput(self):
    while self.stop == False:
      #get keyboard input
      key = self.gameWindow.getch()

      #convert int to ascii
      if key > 0:
        keyString = chr(key)
      else:
        keyString = ""
      if self.stop == True:
        break

      #process keyboard input
      if keyString in self.data["directionalControls"]:
        newDirection = self.data["directionalControls"][keyString]
        #if key is valid add it to the input queue
        if len(self.inputQueue) < 2:
          self.inputQueue.append(newDirection)

      #break if key x is pressed
      elif keyString == "x":
        self.stop = True
        self.resetTimer = True
        break

      #sleep for a bit so we don't waste cpu
      time.sleep(0.01)

  #main program function
  def main(self):
    self.resetGame()
    #show main menu screen
    curses.flushinp()
    key = self.mainMenuHandler()
    #show options screen if key pressed
    if key == "c":
      self.optionsScreen()
    elif key == "x":
      return

    #set up game
    self.setupGame()
    self.previousDirection = "east"
    self.tick()
    self.printBoard()

    #start thread for input
    self.thread = threading.Thread(target=self.getInput)
    self.thread.start()

    #start main program loop
    tickCounter = 0
    while True:
      #debug code
      #tickCounter += 1
      #self.gameWindow.addstr(0, 0, str(tickCounter))
      
      #idk how to do fancy stuff with threading, this works anyways
      #basically it sleeps for a bit and checks if the timer
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

      if len(self.inputQueue) > 0:
        self.direction = self.inputQueue.pop(0)

      #run a tick and stop if game over
      if self.tick() == False:
        #do not game over if the extra turn is enabled
        if (self.extra_turn == True and self.extra_turn_active == False):
          self.extra_turn_active = True
        else:
          self.gameOverHandler()
          self.stop = True
          break
        #break
      else:
        self.extra_turn_active = False

      #refresh the board
      self.printBoard()

    #display game over screen
    curses.flushinp()
    self.gameOverHandler()

    #program will terminate after any key pressed
    self.stop = True
    self.gameWindow.nodelay(0)
    while True:
      char = self.gameWindow.getkey()
      if char == "y":
        self.screen.clear()
        self.screen.refresh()
        return True
      elif char == "n":
        return False

#run the game if this is the main thread
if __name__ == "__main__":
  try:
    #start main program loop
    game = Game()
    while game.main(): pass
      
    #when game ends quit curses
    curses.endwin()

  #quit curses and print exception if there was an error
  except Exception:
    curses.endwin()
    traceback.print_exc()
    game.stop = True