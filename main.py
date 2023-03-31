from kivy.app import App
from kivy.uix.widget import Widget
import socket
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from functools import partial
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.animation import Animation
import time
import select
import threading
import queue

#BROD KOJI BIRAMO I NJEGOVA ORIJENTACIJA
selectedShip = None
orientation = None

#KOORDINATE KOJE SE SALJU PRILIKOM GADJANJA
input_cords = None
used_cords = []

class GameServer():
    def __init__(self):
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buff_size = 2048
        self.hostname = socket.gethostname()
        self.ip = socket.gethostbyname(self.hostname)
        self.localhost_ip = 'localhost'
        self.tcp.bind((self.localhost_ip, 50))
        self.tcp.listen(1)

    def decodeCords(self, msg):
        cords = msg.split(',')
        cords[0] = int(cords[0])
        cords[1] = int(cords[1])
        return cords

class GameClient():
    def __init__(self, ip):
        self.buff_size = 2048
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        buff_size = 1024
        self.tcp.connect((ip, 50))
#        tcp.send('test'.encode())
#        data = tcp.recv(buff_size).decode()
#        print(data)
#        tcp.close

#    def sendData(self, msg):
#        self.tcp.send(msg)

    def decodeCords(self, msg):
        cords = msg.split(',')
        cords[0] = int(cords[0])
        cords[1] = int(cords[1])
        return cords

class Ship:
    def __init__(self, size, name):
        self.name = name
        self.size = size
        self.drowned = False
        self.hit_cords = []
        self.cords = []
        self.health = self.size

        i = 1
        while i <= self.size:
            self.hit_cords.append(False)
            i+=1

    def setCords(self, cord):
        self.cords.append(cord)

    def setHit(self, hit_cord, i):
        self.hit_cords[i] = True
        self.health -= 1
        k = 0

        while k < self.size:
            if self.hit_cords[k] is False:
                self.drowned = False
                break
            else:
                self.drowned = True
            k += 1

        if self.drowned is True:
            #print("DROWNED SHIP")
            pass

    def printData(self):
        print(self.cords)
        print(self.hit_cords)
        print(self.size)
        print(self.drowned)
        print(self.health)

class Field():
    def __init__(self, btn_id, board_map, placed_ships):
        self.btn = Button()
        self.btn.background_color = (0, 135/255, 225/255, 1)
        self.btn_id = btn_id
        self.contains = False

        #PROSLEDJUJEMO SELECTED SHIP DA NE BISMO MENJALI KOD
        self.btn.bind(on_press=lambda x: self.placeShip(board_map, selectedShip,self.decodeCords(btn_id), placed_ships))

    def placeShip(self, board_map, ship, cord, placed_ships):
        i = 1
        exists = False
        placeable = True

        try:
            for s in placed_ships:
                if s.name == ship.name:
                    exists = True
        except AttributeError:
                pass

        try:
            while i <= ship.size:
                try:
                    if orientation == 'Horizontal':
                        if board_map[cord[0]][cord[1] - 1 + i].contains is True:
                            placeable = False
                            break
                    elif orientation == 'Vertical':
                        if board_map[cord[0] - 1 + i][cord[1]].contains is True:
                            placeable = False
                            break
                    elif orientation is None:
                        placeable = False
                        break
                except IndexError:
                    placeable = False
                    break
                i += 1
        except AttributeError:
            placeable = False

        i = 1

        if exists is False and placeable is True:
            while i <= ship.size:
                if orientation == 'Horizontal':
                    board_map[cord[0]][cord[1]-1+i].btn.background_color = (1,1,1,1)
                    board_map[cord[0]][cord[1] - 1 + i].contains = True
                    ship.setCords([cord[0], cord[1]-1+i])
                elif orientation == 'Vertical':
                    board_map[cord[0]-1+i][cord[1]].btn.background_color = (1,1,1,1)
                    board_map[cord[0] - 1 + i][cord[1]].contains = True
                    ship.setCords([cord[0]-1+i, cord[1]])
                i += 1
            placed_ships.append(ship)

    def decodeCords(self, cord_msg):
        cords = cord_msg.split(',')
        decodedCords = [int(cords[1]), int(cords[2])]
        return decodedCords

class targetField():
    def __init__(self, btn_id):
        self.btn_id = btn_id
        self.btn = Button()
        self.btn.background_color = (0, 135/255, 225/255, 1)
        self.hit_cords = self.decodeCords(self.btn_id)
        self.btn.bind(on_press=lambda x: self.on_click())

    def on_click(self):
        global input_cords
        global used_cords

        if self.hit_cords in used_cords:
            input_cords = None
        else:
            #used_cords.append(self.hit_cords)
            input_cords = str(self.hit_cords[0]) + ',' + str(self.hit_cords[1])

    def decodeCords(self, cord_msg):
        cords = cord_msg.split(',')
        decodedCords = [int(cords[1]), int(cords[2])]
        return decodedCords

class chosenShip():
    def __init__(self, ship):
        self.ship = ship
        self.checkbox = CheckBox()
        self.checkbox.group = 'ships'
        self.checkbox.bind(active=lambda x,y:self.bind(ship, self.checkbox.active))

    def bind(self, ship, active):
        global selectedShip
        if active:
            selectedShip = ship
        else:
            selectedShip = None

class Orientation():
    def __init__(self, k):
        self.k = k
        self.checkbox = CheckBox()
        self.checkbox.group = 'orientation'
        self.checkbox.bind(active=lambda x,y:self.bind(self.checkbox.active))

    def bind(self, active):
        global orientation
        if active:
            orientation = self.k
        else:
            orientation = None

class BattleshipGame(Widget):
    data_queue = queue.Queue()
    game_type = ''
    game_start = False
    apply_flag = False
    menu_flag = True
    turns = 0
    lbl_count = 0
    endgame = 'False'

    #BRODOVI
    carrier = Ship(5, 'Carrier')
    battleship = Ship(4, 'Battleship')
    cruiser = Ship(3, 'Cruiser')
    cruiser2 = Ship(3, '2nd Cruiser')
    destroyer = Ship(2, 'Destroyer')

    #NIZOVI ZA BRODOVE
    ships = [carrier, battleship, cruiser, cruiser2, destroyer]
    placed_ships = []

    #LAYOUTS ZA EKRAN
    preGameGrid = GridLayout
    boardGrid = GridLayout
    targetGrid = GridLayout
    clearGrid = GridLayout
    applyGrid = GridLayout
    endGrid = GridLayout
    menuGrid = GridLayout

    info_label = Label(text='')
    info_label.opacity = 0

    x1, x2 = 0, targetGrid.x

    #MAPE
    board = None
    targetBoard = None

    #DUGMICI
    clear_button = None
    applyButton = None

    anim_function = None
    game_loop = None

    #SERVERSKE PROMENLJIVE
    s = None
    con = None
    c = None
    addr = None

    def mainMenu(self):
        lbl = Label(text='BATTLESHIP', font_size=32, color=(1,1,1,1), outline_color=(0,0,0,1), outline_width=2)
        btn = Button(text='HOST SERVER')
        btn2 = Button(text='JOIN SERVER')
        self.menuGrid.add_widget(lbl)
        self.menuGrid.add_widget(btn)
        self.menuGrid.add_widget(btn2)

        btn.bind(on_press=lambda x: self.hostServer())
        btn2.bind(on_press=lambda x: self.joinServerMenu())


    def hostServer(self):
        self.game_type = 's'
        self.s = GameServer()
        self.menuGrid.clear_widgets()
        lbl = Label(text='WAITING FOR CONNECTION...')
        lbl2 = Label(text=self.s.localhost_ip)
        self.menuGrid.add_widget(lbl)
        self.menuGrid.add_widget(lbl2)
        event = Clock.create_trigger(self.accept)
        event()

    def accept(self, *largs):
        self.con, self.addr = self.s.tcp.accept()
        self.preGame()

    def joinServerMenu(self):
        self.game_type = 'c'
        self.menuGrid.clear_widgets()
        txt_input = TextInput(hint_text='INPUT IP ADDRESS', multiline=False, on_text_validate=lambda x: self.joinServer(txt_input.text, lbl))
        btn = Button(text='JOIN')
        lbl = Label(text='INVALID IP', opacity=0, color=(1,1,1,1), outline_width=2, outline_color=(0,0,0,1))
        self.menuGrid.add_widget(txt_input)
        self.menuGrid.add_widget(btn)
        self.menuGrid.add_widget(lbl)
        btn.bind(on_press=lambda x: self.joinServer(txt_input.text, lbl))

    def joinServer(self, ip, lbl):
        try:
            self.c = GameClient(ip)
            self.addr = ip
            self.preGame()
        except OSError:
            lbl.opacity=100

    def preGame(self):
        self.menu_flag = False
        self.menuGrid.clear_widgets()

        self.board = self.createBoard(self.boardGrid, 'b')
        self.targetBoard = self.createBoard(self.targetGrid, 't')

        self.clear_button = Button(text="Clear Board")
        self.clear_button.bind(on_press=lambda x: self.resetBoard())
        self.clearGrid.add_widget(self.clear_button)

        self.applyButton = Button(text="Apply & Start")
        self.applyButton.bind(on_press=lambda x: self.apply())

        orientation_label = Label(text='Ship Orientation', font_size=20, color=(1,1,1,1), outline_width=2, outline_color=(0,0,0,1))
        empty_label = Label()
        self.preGameGrid.add_widget(orientation_label)
        self.preGameGrid.add_widget(empty_label)

        orientation_array = ['Horizontal', 'Vertical']
        for k in range (2):
            toggle_btn = Orientation(orientation_array[k])
            label = Label(text=orientation_array[k], color=(1,1,1,1), outline_width=2, outline_color=(0,0,0,1))
            self.preGameGrid.add_widget(toggle_btn.checkbox)
            self.preGameGrid.add_widget(label)

        ship_label = Label(text='Ships', font_size=20, color=(1,1,1,1), outline_width=2, outline_color=(0,0,0,1))
        self.preGameGrid.add_widget(ship_label)
        empty_label = Label()
        self.preGameGrid.add_widget(empty_label)

        for i in self.ships:
            checkbox = chosenShip(i)
            label=Label(text=i.name, color=(1,1,1,1), outline_width=2, outline_color=(0,0,0,1))
            self.preGameGrid.add_widget(checkbox.checkbox)
            self.preGameGrid.add_widget(label)

    def resetBoard(self):
        global selectedShip
        global orientation
        self.preGameGrid.clear_widgets()
        self.boardGrid.clear_widgets()
        self.targetGrid.clear_widgets()
        self.clearGrid.clear_widgets()
        self.placed_ships = []
        self.applyGrid.clear_widgets()
        self.apply_flag = False
        selectedShip = None
        orientation = None
        for ship in self.ships:
            ship.cords = []
        self.preGame()

    def createBoard(self, grid, k):
        boardMap = []
        if k == 'b':
            for y in range(10):
                boardMap.append([])
                for x in range(10):
                    btn_id = k + ',' + str(y) + ',' + str(x)
                    btn = Field(btn_id, boardMap, self.placed_ships)
                    boardMap[y].append(btn)
                    grid.add_widget(btn.btn)
        if k == 't':
            for y in range(10):
                boardMap.append([])
                for x in range(10):
                    btn_id = k + ',' + str(y) + ',' + str(x)
                    btn = targetField(btn_id)
                    boardMap[y].append(btn)
                    grid.add_widget(btn.btn)
        return boardMap

    def printMap(self, board_map):
        for y in range(10):
            print(board_map[y])

    def target(self, hit_cord, board_map):
        i = 0
        global input_cords

        if board_map[hit_cord[0]][hit_cord[1]].contains is True:
            for k in range(5):
                while i < self.ships[k].size:
                    if self.ships[k].cords[i] == hit_cord:
                        self.ships[k].setHit(hit_cord, i)
                        board_map[hit_cord[0]][hit_cord[1]].btn.background_color = (1, 0, 0, 1)
                        if self.ships[k].drowned is True:
                            return 'True,'+str(self.ships[k].name)+',True'
                        else:
                            return 'True,'+str(self.ships[k].name)+',False'
                    i += 1
                i = 0

        elif board_map[hit_cord[0]][hit_cord[1]].contains is False:
            return 'False,None,False'

    def updateTargetBoard(self, hit_cord, result, ship, drowned, board_map):
        if self.lbl_count % 2 != 0:
            self.info_label.opacity = 0
            self.lbl_count += 1
        if result == 'True':
            board_map[hit_cord[0]][hit_cord[1]].btn.background_color = (1, 0, 0, 1)
        elif result == 'False':
            board_map[hit_cord[0]][hit_cord[1]].btn.background_color = (1, 1, 1, 1)

        if drowned == 'True':
            text = ship+' has been drowned!'
            self.info_label.text = text
            self.info_label.opacity = 100
            self.lbl_count += 1

    def animation(self, *largs):
        if self.boardGrid.x != 75 and self.targetGrid.x != self.x2 - 75:
            self.boardGrid.x += 1
            self.targetGrid.x -= 1
        else:
            self.game_start = True

    def apply(self):
        self.preGameGrid.clear_widgets()
        self.clearGrid.clear_widgets()
        self.applyGrid.clear_widgets()
        self.turns += 1
        self.anim_function = Clock.schedule_interval(partial(self.animation), 1 / 30.)

    def checkBoard(self, *largs):
        if len(self.placed_ships) == 5 and self.apply_flag is False and self.menu_flag is False:
            self.apply_flag = True
            self.applyGrid.add_widget(self.applyButton)

    def wait(self, s, c, con):
        if self.game_type == 's':
            #CEKAMO DA KLIJENT GADJA
            data = con.recv(s.buff_size).decode()
            if data == 'True':
                self.gameOver(s, c, con)
            else:
                con.send(self.target(s.decodeCords(data), self.board).encode())
                t = con.recv(s.buff_size).decode()
                self.turns = int(t)

        elif self.game_type == 'c':
            #CEKAMO DA SERVER GADJA
            data = c.tcp.recv(c.buff_size).decode()
            if data == 'True':
                self.gameOver(s, c, con)
            else:
                c.tcp.send(self.target(c.decodeCords(data), self.board).encode())
                t = c.tcp.recv(c.buff_size).decode()
                self.turns = int(t)

    def chooseTarget(self, s, c, con):
        global input_cords
        global used_cords
        if input_cords is not None:
            if self.game_type == 's':
                #SERVER GADJA
                if input_cords not in used_cords:
                    used_cords.append(input_cords)
                    con.send(input_cords.encode())
                    data = con.recv(s.buff_size).decode()
                    results = data.split(',')
                    self.updateTargetBoard(s.decodeCords(input_cords), results[0],  results[1], results[2], self.targetBoard)
                    if results[0] == 'True':
                        self.turns += 1
                    self.turns += 1
                    con.send(str(self.turns).encode())
                    input_cords = None

            elif self.game_type == 'c':
                # KLIJENT GADJA
                if input_cords not in used_cords:
                    used_cords.append(input_cords)
                    c.tcp.send(input_cords.encode())
                    data = c.tcp.recv(c.buff_size).decode()
                    results = data.split(',')
                    self.updateTargetBoard(c.decodeCords(input_cords), results[0],  results[1], results[2], self.targetBoard)
                    if results[0] == 'True':
                        self.turns += 1
                    c.tcp.send(str(self.turns).encode())
                    input_cords = None

    def gameCheck(self, event, *largs):
        self.gameLoop(self.s, self.c, self.con, event)

    def gameLoop(self, s, c, con, event, *largs):
        if self.game_start is True:
            event.cancel()
            self.anim_function.cancel()

            i = 0

            for ship in self.ships:
                if ship.drowned is False:
                    self.endgame = 'False'
                    break
                else:
                    self.endgame = 'True'

            if self.endgame == 'True':
                if self.game_type == 's':
                    con.send(self.endgame.encode())
                    self.gameOver(s, c, con)
                else:
                    c.tcp.send(self.endgame.encode())
                    self.gameOver(s, c, con)

            else:
                if self.game_type == 's':
                    if self.turns % 2 != 0:
                        self.wait(s, c, con)
                    elif self.turns % 2 == 0:
                        self.chooseTarget(s, c, con)

                if self.game_type == 'c':
                    if self.turns % 2 == 0:
                        self.wait(s, c, con)
                    if self.turns % 2 != 0:
                        self.chooseTarget(s, c, con)

    def gameOver(self, s, c, con):
        self.game_loop.cancel()
        for ship in self.ships:
            if ship.drowned is False:
                text = 'YOU WIN!'
                break
            else:
                text = 'YOU LOSE!'

        lbl = Label(text=text, font_size = 20)
        btn = Button(text='QUIT')
        self.endGrid.add_widget(lbl)
        self.endGrid.add_widget(btn)

        btn.bind(on_press=lambda x: self.quitGame(con, c))

    def quitGame(self, con, c):
        if self.game_type == 's':
            con.close()
        else:
            c.tcp.close()
        quit()

class BattleshipApp(App):
    def build(self):
        game = BattleshipGame()
        game.mainMenu()

        check_board = Clock.schedule_interval(partial(game.checkBoard), 1 / 30.)
        game.game_loop = Clock.schedule_interval(partial(game.gameCheck, check_board), 1 / 30.)

        return game

if __name__ == '__main__':
   BattleshipApp().run()
