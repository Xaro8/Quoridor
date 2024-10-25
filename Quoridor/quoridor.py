import pygame as py
from math import floor
from random import random
from collections import deque

WIDTH = 1280
HEIGHT = 720
CRAD = 49
BSCALE = 0.6
DEFAULT = [(-1, 0), (1, 0), (0, -1), (0, 1)]
WALLSINIT = [
    (60, 60),
    (WIDTH - 240, HEIGHT - 200),
    (60, HEIGHT - 200),
    (WIDTH - 240, 60),
]
OFFSET = 10


class Player:
    """Represents a player in the game."""
    
    def __init__(self, colour, position, walls):
        """
        Initializes the player.

        Args:\n
            colour (str): The color of the player.
            position (tuple): The starting position of the player.
            walls (int): The number of walls the player has.
        """
        self.colour = colour
        self.position = position
        self.remaining_walls = walls
        self.won = False
        if self.position[1] == 4:
            self.wins = (8 - self.position[0], -1)
        elif self.position[0] == 4:
            self.wins = (-1, 8 - self.position[1])

    def setpos(self, position):
        """
        Sets the player's position and checks if they have won.

        Args:\n
            position (tuple): The new position of the player.
        """
        self.position = position
        if int(self.position[0]) == int(self.wins[0]) or int(self.position[1]) == int(self.wins[1]):
            self.won = True

    def place_wall(self):
        """Decreases the player's remaining walls by one."""
        self.remaining_walls -= 1

    def draw(self, screen):
        """
        Draws the player on the screen.

        Args:\n
            screen (pygame.Surface): The surface to draw the player on.
        """
        cords = (
            self.position[0] * 122 * BSCALE + 580 * BSCALE,
            self.position[1] * 122 * BSCALE + 112 * BSCALE,
        )
        py.draw.circle(screen, self.colour, cords, 49 * BSCALE)
        py.draw.circle(screen, "white", cords, 49 * BSCALE, width=2)


class Bot(Player):
    """Represents a bot player in the game."""

    def __init__(self, colour, position, walls, validator):
        """
        Initializes the bot player.

        Args:\n
            colour (str): The color of the bot.
            position (tuple): The starting position of the bot.
            walls (int): The number of walls the bot has.
            validator (Validator): The validator for making moves and placing walls.
        """
        super().__init__(colour, position, walls)
        self.validator = validator

    def make_move(self):
        """
        Determines the bot's move.

        Returns:\n
            tuple: The move type and move position or wall orientation.
        """
        placewall = False
        if self.remaining_walls != 0 and random() > 0.75:
            placewall = True
        if placewall:
            bwall = self.validator.best_wall(self.position, self.wins)
            return "orient", bwall
        else:
            bmove, bscore = self.validator.best_move(self.position, self.wins)
            return "move", bmove


class Wall:
    """Represents a wall in the game."""

    def __init__(self, start, end, fake=False):
        """
        Initializes the wall.

        Args:\n
            start (tuple): The start position of the wall.
            end (tuple): The end position of the wall.
            fake (bool, optional): If the wall is fake. Defaults to False.
        """
        x, y = start
        dx, dy = end

        if not fake:
            x, y = x + 0.5, y + 0.5
            dx, dy = dx + 0.5, dy + 0.5

        self.start = (x, y)
        self.end = (dx, dy)

        if self.start[0] > self.end[0] or self.start[1] > self.end[1]:
            self.start, self.end = self.end, self.start

    def draw(self, screen):
        """
        Draws the wall on the screen.

        Args:\n
            screen (pygame.Surface): The surface to draw the wall on.
        """
        cords1 = (
            floor(self.start[0]) * 122 * BSCALE + 642 * BSCALE,
            floor(self.start[1]) * 122 * BSCALE + 173 * BSCALE,
        )
        cords2 = (
            floor(self.end[0]) * 122 * BSCALE + 642 * BSCALE,
            floor(self.end[1]) * 122 * BSCALE + 173 * BSCALE,
        )
        py.draw.line(
            screen, "brown2", start_pos=cords1, end_pos=cords2, width=int(10 * BSCALE)
        )

    def overlaps(self, other):
        """
        Checks if the wall overlaps with another wall.

        Args:\n
            other (Wall): Another wall to check overlap with.

        Returns:\n
            bool: True if the walls overlap, False otherwise.
        """
        if self.start == other.start and self.end == other.end:
            return True
        if (
            self.start[0] < other.end[0] < self.end[0]
            and self.start[1] == self.end[1] == other.end[1] == other.start[1]
        ):
            return True
        if (
            self.start[0] < other.start[0] < self.end[0]
            and self.start[1] == self.end[1] == other.end[1] == other.start[1]
        ):
            return True
        if (
            self.start[1] < other.end[1] < self.end[1]
            and self.start[0] == self.end[0] == other.end[0] == other.start[0]
        ):
            return True
        if (
            self.start[1] < other.start[1] < self.end[1]
            and self.start[0] == self.end[0] == other.end[0] == other.start[0]
        ):
            return True
        if (
            self.start[1] < other.start[1] < self.end[1]
            and other.start[0] < self.start[0] < other.end[0]
        ):
            return True
        if (
            self.start[0] < other.start[0] < self.end[0]
            and other.start[1] < self.start[1] < other.end[1]
        ):
            return True
        return False


class Validator:
    """Validates moves and walls in the game."""

    def __init__(self, grid, walls, players):
        """
        Initializes the validator.

        Args:\n
            grid (list): The game grid.
            walls (list): The list of walls in the game.
            players (list): The list of players in the game.
        """
        self.visited = set()
        self.grid = grid
        self.walls = walls
        self.players = players

    def reset(self):
        self.visited = set()

    def possible_moves(self, pos):
        """
        Gets possible moves for a position.

        Args:\n
            pos (tuple): The current position.

        Returns:\n
            list: The list of possible move positions.
        """
        ret = []
        for dx, dy in DEFAULT:
            x, y = pos
            if 0 <= x + dx < 9 and 0 <= y + dy < 9:
                if self.grid[x + dx][y + dy] is not None:
                    if (
                        0 <= x + dx * 2 < 9
                        and 0 <= y + dy * 2 < 9
                        and self.grid[x + dx * 2][y + dy * 2] is None
                        and not self.any_overlap((x, y), (x + 2 * dx, y + 2 * dy), True)
                    ):
                        ret.append((x + 2 * dx, y + 2 * dy))
                    else:
                        if (
                            dy != 0
                            and x + 1 < 9
                            and self.grid[x + 1][y + dy] is None
                            and not self.any_overlap((x, y), (x + 1, y + dy), True)
                        ):
                            ret.append((x + 1, y + dy))
                        if (
                            dy != 0
                            and x - 1 >= 0
                            and self.grid[x - 1][y + dy] is None
                            and not self.any_overlap((x, y), (x - 1, y + dy), True)
                        ):
                            ret.append((x - 1, y + dy))
                        if (
                            dx != 0
                            and y + 1 < 9
                            and self.grid[x + dx][y + 1] is None
                            and not self.any_overlap((x, y), (x + dx, y + 1), True)
                        ):
                            ret.append((x + dx, y + 1))
                        if (
                            dx != 0
                            and y - 1 >= 0
                            and self.grid[x + dx][y - 1] is None
                            and not self.any_overlap((x, y), (x + dx, y - 1), True)
                        ):
                            ret.append((x + dx, y - 1))
                elif not self.any_overlap((x, y), (x + dx, y + dy), True):
                    ret.append((x + dx, y + dy))
        return ret

    def any_overlap(self, start, end, fake=False):
        """
        Checks if any wall overlaps between two positions.

        Args:\n
            start (tuple): The start position.
            end (tuple): The end position.
            fake (bool, optional): If the wall is fake. Defaults to False.

        Returns:\n
            bool: True if any wall overlaps, False otherwise.
        """
        check = Wall(start, end, fake)
        for wall in self.walls:
            if check.overlaps(wall):
                return True
        return False

    def possible_walls(self, player):
        """
        Returns list of all possible starts of wall.

        Args:\n
            player (Player): only for number of walls left for player. 
        Returns:\n
            list: tuple list of all possible starts of wall.
        """
        ret = []
        if player.remaining_walls == 0:
            return ret

        for y in range(8):
            for x in range(8):
                if self.possible_orients((x, y)) != []:
                    ret.append((x, y))

        return ret

    def possible_orients(self, pos):
        """
        Returns list of all possible orientations of wall in current position.

        Args:\n
            pos (tuple): Start of the wall to check. 
        Returns:\n
            list: tuple list of all directions wall can face in give position.
        """
        ret = []
        for dx, dy in DEFAULT:
            end = (pos[0] + 2 * dx, pos[1] + 2 * dy)
            if -1 <= end[0] < 9 and -1 <= end[1] < 9:
                if not self.any_overlap(pos, end):
                    can = True
                    self.walls.append(Wall(pos, end))
                    for player in self.players:
                        self.reset()
                        if not self.way_exists(player.position, player.wins):
                            can = False
                            break
                    del self.walls[-1]
                    if can:
                        ret.append((dx, dy))
        return ret

    def way_exists(self, node, dest):
        """
        Depth-first search to find connection between nodes.

        Args:\n
            node (tuple): The current node.
            dest (tuple): The destination node.
        Returns:\n
            bool: True if the end node is reachable, False otherwise.
        """

        if node[0] == dest[0] or node[1] == dest[1]:
            return True
        else:
            # print(node)
            self.visited.add(node)
            for dx, dy in DEFAULT:
                end = (node[0] + dx, node[1] + dy)
                if (
                    0 <= end[0] < 9
                    and 0 <= end[1] < 9
                    and end not in self.visited
                    and not self.any_overlap(node, end, True)
                ):
                    if self.way_exists(end, dest):
                        return True
            return False

    def bfs(self, pos, wins):
        """
        Breadth-first search to find shortest way between nodes.

        Args:\n
            pos (tuple): The current position.
            wins (tuple): The destination nodes.
        Returns:\n
            int: Length of shortest path to win.
        """
        queue = deque()
        self.reset()
        queue.append((pos, 0))
        self.visited.add(pos)
        while queue:
            curr, depth = queue.popleft()

            if curr[0] == wins[0] or curr[1] == wins[1]:
                return depth
            for move in self.possible_moves(curr):
                if move not in self.visited:
                    self.visited.add(move)
                    queue.append((move, depth + 1))
        return 1000000

    def best_move(self, start, wins):
        """
        Determines the best move for the player.

        Args:\n
            start (tuple): The start position.
            wins (tuple): The wining positions.

        Returns:\n
            tuple: The best move for the player.
        """
        moves = self.possible_moves(start)
        bmove, bscore = moves[0], self.bfs(moves[0], wins)
        for move in moves:
            score = self.bfs(move, wins)
            if score < bscore:
                bmove = move
                bscore = score
        return bmove, bscore

    def all_possible_walls(self):
        """
        Returns list of all possible walls.

        Args:\n

        Returns:\n
            list: tuple list of all possible starts of wall.
        """
        ret = []
        for y in range(8):
            for x in range(8):
                for dist in self.possible_orients((x, y)):
                    ret.append(((x, y), (dist)))
        return ret

    def best_wall(self, my_pos, win):
        """
        Determines the best wall placement for the player.

        Args:\n
            my_pos (tuple): Position of my player.
            win (tuple): The winning positions.

        Returns:\n
            tuple: The best wall placement for player.
        """
        all_w = self.all_possible_walls()
        samples = all_w
        bwall, bscore = None, -1000

        for pos, dir in samples:
            score = 0
            self.walls.append(Wall(pos, (pos[0] + 2 * dir[0], pos[1] + 2 * dir[1])))
            for player in self.players:
                if player.position != my_pos:
                    # print(pos,player.position)
                    score += self.bfs(player.position, player.wins)
            score -= self.bfs(my_pos, win)
            del self.walls[-1]
            if score > bscore:
                bwall = (pos, dir)
                bscore = score
        return bwall


class Board:
    """Implements game board handling"""

    def __init__(self):
        """
        Initializes the board.
        """
        self.walls = []
        self.grid = []
        for _ in range(9):
            self.grid.append([None] * 9)

    def print(self):
        """
        Prints the board like text.
        """
        print(self.grid)

    def move(self, fr, to):
        """
        Changes position of players.

        Args:\n
            fr (tuple) : Position to move player from
            to (tuple) : Position to move player to
        """
        x, y = fr
        dx, dy = to
        self.grid[dx][dy] = self.grid[x][y]
        self.grid[x][y] = None

    def place_wall(self, pos, orient):
        """
        Adds new wall to list of walls.

        Args:\n
            pos (tuple) : Starting point of wall.
            orient (tuple) : Direction in which wall is facing.
        """
        x, y = pos
        dx, dy = orient
        self.walls.append(Wall((x, y), (x + 2 * dx, y + 2 * dy)))


class Game:
    """
    Implements all functions needed for game loop.
    """
    def __init__(self, num_players, screen_rect):
        """
        Initializes game.

        Args:\n
            num_players (int) : Number of players playing game.
            screen_rect (pygame.Rect) : Rect of screen surface.
        """
        self.board = Board()
        self.currplayer = 0
        self.num_players = num_players

        self.board_img = py.image.load(
            "textures/board" + str(self.num_players) + ".png"
        )
        self.board_img = py.transform.scale(
            self.board_img,
            (self.board_img.get_width() * BSCALE, self.board_img.get_width() * BSCALE),
        )
        self.board_rect = self.board_img.get_rect(center=screen_rect.center)
        self.players = []
        self.font = py.font.SysFont("Calibri", 30)
        self.validator = Validator(self.board.grid, self.board.walls, self.players)

        if num_players == 2:
            self.players += [
                Player("darkgreen", (4, 0), 10),
                Player("slateblue", (4, 8), 10),
            ]
        else:
            self.players += [
                Player("darkgreen", (4, 0), 5),
                Player("gold", (8, 4), 5),
                Player("slateblue", (4, 8), 5),
                Player("plum", (0, 4), 5),
            ]

        for i in range(num_players):
            x, y = self.players[i].position
            self.board.grid[x][y] = i

    def possible_moves(self):
        """
        Returns all possible moves for current player and it's color.
        """
        return self.validator.possible_moves(
            self.players[self.currplayer].position
        ), self.players[self.currplayer].colour

    def possible_walls(self):
        """
        Returns all possible starts of walls for current player.
        """
        return self.validator.possible_walls(self.players[self.currplayer])

    def possible_orients(self, pos):
        """
        Returns all possible orientations of walls in given position.

        Args:\n
            pos (tuple) : Position of wall start 
        """
        return self.validator.possible_orients(pos)

    def make_move(self, type, pos, orient=None):
        """
        Makes move of some type by currents player.

        Args:\n
            type (string) : Type of move (wall/move)
            pos (tuple) : Position of wall start / Position to which change current player position changes.
            orient (tuple) : Direction  of wall placed (optional) 
        """
        if type == "wall":
            self.board.place_wall(pos, orient)

            self.players[self.currplayer].place_wall()
            self.currplayer += 1
            self.currplayer %= self.num_players

        elif type == "move":
            self.board.move(self.players[self.currplayer].position, pos)
            self.players[self.currplayer].setpos(pos)
            self.currplayer += 1
            self.currplayer %= self.num_players

    def draw(self, screen):
        """
        Displays game.

        Args:\n
            screen (pygame.Surface) : Suurface on which game will be displayed.
        """
        screen.blit(self.board_img, self.board_rect)

        for i in range(len(self.players)):
            player = self.players[i]
            player.draw(screen)
            x, y = WALLSINIT[i]
            hm = None
            for j in range(player.remaining_walls):
                hm = py.draw.rect(screen, player.colour, py.Rect(x, y, 180, 60))
                py.draw.rect(screen, "black", py.Rect(x, y, 180, 60), width=2)
                y += 10
            if hm is not None:
                num_te = self.font.render(str(player.remaining_walls), True, "black")
                num_te_re = num_te.get_rect(center=hm.center)
                screen.blit(num_te, num_te_re)

        for wall in self.board.walls:
            wall.draw(screen)

    def setbots(self, bots):
        """
        Sets which players are bots.

        Args:\n
            bots (list) : Tells which players were chosen to be bots.
        """
        if self.num_players == 2:
            if bots[0]:
                self.players[0] = Bot("darkgreen", (4, 0), 10, self.validator)
            if bots[1]:
                self.players[1] = Bot("slateblue", (4, 8), 10, self.validator)
        else:
            if bots[0]:
                self.players[0] = Bot("darkgreen", (4, 0), 5, self.validator)
            if bots[1]:
                self.players[1] = Bot("gold", (8, 4), 5, self.validator)
            if bots[2]:
                self.players[2] = Bot("slateblue", (4, 8), 5, self.validator)
            if bots[3]:
                self.players[3] = Bot("plum", (0, 4), 5, self.validator)


class MenuButton(py.sprite.Sprite):
    """
        Implements menu buttons.
    """
    def __init__(self, filename, location, type, args, scale=1.0):
        """
            Initializes sprite.

            Args:\n
                filename (string) : from which file image of button will be loaded.
                location (tuple) : where button will be placed
                type (string) : what type of button is it
                args (list) : all other needed arguments
                scale (float) : scale of loaded images
        """
        self.args = args
        self.type = type
        self.img = py.image.load(filename)
        self.img = py.transform.scale_by(self.img, scale)
        self.rect = self.img.get_rect()
        self.rect.topleft = location


class MoveButton(py.sprite.Sprite):
    """
        Implements movement buttons.
    """
    def __init__(self, location, type, args, scale, screen):
        """
            Initializes sprite.

            Args:\n
                location (tuple) : where button will be placed
                type (string) : what type of button is it
                args (list) : all other needed arguments
                scale (float) : scale of loaded images
                screen (pygame.Surface) : surface on which button will be displayed.
        """
        self.args = args[2]
        self.type = type
        self.rect = py.draw.circle(
            screen, args[1], (location), args[0] * scale, width=2
        )


class WallButton(py.sprite.Sprite):
    """
        Implements walls buttons.
    """
    def __init__(self, location, type, args, screen=None):
        """
            Initializes sprite.

            Args: \n
                location (tuple) : where button will be placed 
                type (string) : what type of button is it
                args (list) : all other needed arguments
                scale (float) : scale of loaded images
                screen (pygame.Surface) : surface on which button will be displayed.
        """
        self.type = type
        self.args = args[2]
        self.rect = py.draw.line(
            screen, args[1], start_pos=location, end_pos=args[3], width=args[0]
        )


class CheckBox(py.sprite.Sprite):
    """
        Implements checkboxes. 
    """
    def __init__(self, checkmark_file, location, type, checked,poz):
        """
            Initializes sprite.
            
            Args:\n
                checkmark_file (pygame.Surface) : loaded image of checkmark
                location (tuple) : where button will be placed
                type (string) : what type of button is it
                cheked (bool) : tells if checkbox is checked

        """
        self.type = type
        self.checked = checked
        self.img = checkmark_file
        self.rect = self.img.get_rect()
        self.rect.topleft = location
        self.poz =  poz


class UImanager:
    """
    The UImanager class is responsible for managing the user interface of the game "QUORIDOR".
    It handles the initialization of the game window, loading of graphical assets, and the display of
    various game states such as the menu, game board, and endgame screens.
    """
        
    def __init__(self):
        """
        Initializes the UImanager instance by setting up the game window, loading images,
        creating buttons, and initializing other UI components.
        """
        py.init()
        py.sprite.Sprite.__init__(self)
        py.font.init()
        py.display.set_caption("QUORIDOR")
        self.screen = py.display.set_mode((WIDTH, HEIGHT))
        self.screen_rect = self.screen.get_rect()

        self.background = py.image.load("textures/background-table.png")
        self.background = py.transform.scale_by(self.background, 0.334)

        self.button2 = MenuButton(
            "textures/menubutton2.png", (240, 400), "MODE", 2, 0.3
        )
        pos4 = (self.screen_rect.width - 240 - self.button2.img.get_width(), 400)
        self.button4 = MenuButton("textures/menubutton4.png", pos4, "MODE", 4, 0.3)

        self.reset = MenuButton(
            "textures/resetbutton.png", (240, 400), "RESET", None, 0.3
        )
        self.quit = MenuButton("textures/quitbutton.png", pos4, "QUIT", None, 0.3)

        self.checkbox = py.image.load("textures/checkbox.png")
        self.checkmark = py.image.load("textures/checkmark.png")
        self.checkbox = py.transform.scale_by(self.checkbox, 0.5)
        self.checkmark = py.transform.scale_by(self.checkmark, 0.5)

        self.colors = ["darkgreen", "slateblue", "gold", "plum"]
        self.active = [self.button2, self.button4]
        self.checked = [False, False, False, False]
        self.fullscreen = False

    def get(self):
        """
        Handles user input events such as mouse clicks and key presses, and returns the type of action
        and associated arguments.
        
        Returns:\n
            tuple: (action_type, action_args)
        """
        for event in py.event.get():
            match event.type:
                case py.QUIT:
                    return "QUIT", ""
                case py.MOUSEBUTTONDOWN:
                    pos = py.mouse.get_pos()
                    for sprite in self.active:
                        if sprite.rect.collidepoint(pos):
                            if sprite.type == "checkbox":
                                self.checked[sprite.poz] = not self.checked[sprite.poz]
                            else:
                                return sprite.type, sprite.args
                case py.KEYDOWN:
                    match event.key:
                        case py.K_SPACE:
                            return "START", self.checked
                        case py.K_ESCAPE:
                            return "endtodelete", []

        return "STANDBY", ""

    def display_menu(self):
        """
        Displays the main menu of the game, including the title and game mode selection buttons.
        """
        self.screen.blit(self.background, (0, 0))
        menu_font = py.font.SysFont("Calibry", 260, True)
        menu_text = menu_font.render("QUORIDOR", True, "grey29")
        menu_text_out = menu_font.render("QUORIDOR", True, "white")
        menu_re = menu_text.get_rect(center=(WIDTH / 2, HEIGHT / 3))

        self.screen.blit(self.button2.img, self.button2.rect)
        self.screen.blit(self.button4.img, self.button4.rect)

        x, y = menu_re.topleft
        self.screen.blit(menu_text_out, (x - 5, y - 5))
        self.screen.blit(menu_text_out, (x - 5, y + 5))
        self.screen.blit(menu_text_out, (x + 5, y - 5))
        self.screen.blit(menu_text_out, (x + 5, y + 5))

        self.screen.blit(menu_text, menu_re)
        self.active = [self.button2, self.button4]

    def display_game(self, game):
        """
        Displays the game board, including possible moves and wall placements based on the current game state.
        
        Args:\n
            game (Game): The current game instance.
        """
        self.screen.blit(self.background, (0, 0))
        self.active = []
        game.draw(self.screen)
        moves, colr = game.possible_moves()
        for move in moves:
            cords = (
                move[0] * 122 * BSCALE + 580 * BSCALE,
                move[1] * 122 * BSCALE + 112 * BSCALE,
            )
            self.active.append(
                MoveButton(cords, "move", (44, colr, move), BSCALE, self.screen)
            )

        walls = game.possible_walls()

        for wall in walls:
            cords = (
                wall[0] * 122 * BSCALE + 643 * BSCALE,
                wall[1] * 122 * BSCALE + 175 * BSCALE,
            )
            self.active.append(
                MoveButton(
                    cords, "wallchoose", (10, "white", wall), BSCALE, self.screen
                )
            )

    def display_orientations(self, game, pos, col="grey"):
        """
        Displays possible orientations for wall placements in the game.
        
        Args:\n
            game (Game): The current game instance.
            pos (tuple): The position of the wall.
            col (str, optional): The color of the wall. Defaults to "grey".
        """
        self.display_game(game)
        for dx, dy in game.possible_orients(pos):
            cords1 = (
                (pos[0] + 0.25 * dx) * 122 * BSCALE + 642 * BSCALE,
                (pos[1] + 0.25 * dy) * 122 * BSCALE + 173 * BSCALE,
            )
            cords2 = (
                (pos[0] + 1.75 * dx) * 122 * BSCALE + 642 * BSCALE,
                (pos[1] + 1.75 * dy) * 122 * BSCALE + 173 * BSCALE,
            )

            self.active.append(
                WallButton(
                    cords1,
                    "orient",
                    (int(10 * BSCALE), col, (dx, dy), cords2),
                    self.screen,
                )
            )

    def display_endgame(self, colour):
        """
        Displays the endgame screen showing the winning player.
        
        Args:\n
            colour (str): The color of the winning player.
        """
        self.screen.blit(self.background, (0, 0))
        end_font = py.font.SysFont("Calibry", 150, True)
        won_text = end_font.render("Player won!", True, (0, 0, 0))
        if colour == "white":
            who_text = end_font.render(str.capitalize("None"), True, colour)
        else:
            who_text = end_font.render(str.capitalize(colour), True, colour)

        who_text_re = who_text.get_rect(center=(WIDTH / 2, HEIGHT / 4))
        won_text_re = won_text.get_rect(midtop=who_text_re.midbottom)

        self.active = [self.reset, self.quit]

        self.screen.blit(won_text, won_text_re)
        self.screen.blit(who_text, who_text_re)
        self.screen.blit(self.reset.img, self.reset.rect)
        self.screen.blit(self.quit.img, self.quit.rect)

    def choose_bots(self, howmuch):
        """
        Displays the screen for selecting which players are controlled by bots.
        
        Args:\n
            howmuch (int): The number of players to choose bots for.
        """
        self.screen.blit(self.background, (0, 0))
        self.active = []

        choose_font = py.font.SysFont("Calibry", 150, True)
        colors_font = py.font.SysFont("Calibry", 70, True)
        text = choose_font.render("CHOOSE BOTS:", True, (0, 0, 0))
        text_re = text.get_rect(center=(WIDTH / 2, HEIGHT / 4))
        self.screen.blit(text, text_re)
        hint = colors_font.render("*press SPACE to continue*", True, "grey29")
        hint_re = hint.get_rect(midbottom=self.screen_rect.midbottom)
        self.screen.blit(hint, hint_re)
        for i in range(howmuch):
            self.active.append(
                CheckBox(
                    self.checkmark,
                    (
                        (i * 2 + 1) * WIDTH // (howmuch * 2 + howmuch * 1 / 2),
                        HEIGHT * 1 / 2,
                    ),
                    "checkbox",
                    self.checked[i],
                    i
                )
            )

        for i in range(howmuch):
            box = self.active[i]
            color_p = colors_font.render(
                self.colors[i].capitalize(), True, self.colors[i]
            )
            color_re = color_p.get_rect()
            color_re.midbottom = box.rect.midtop
            self.screen.blit(self.checkbox, box.rect)
            self.screen.blit(color_p, color_re)
            if box.checked:
                self.screen.blit(box.img, box.rect)


class Quoridor:
    """
    The Quoridor class manages the overall game logic and flow. It handles transitions between different
    game states such as menu, game, and endgame, and processes player actions and bot moves.
    """
    def __init__(self):
        """
        Initializes the Quoridor instance, setting the initial game state, creating the UImanager instance,
        and initializing game components.
        """
        self.state = "menu"
        self.game = None
        self.ui = UImanager()
        self.clock = py.time.Clock()
        self.running = True
        self.clicked_pos = None
        self.game = Game(2, self.ui.screen_rect)
        self.num_players = 2
        self.wincol = "white"

    def game_loop(self):
        """
        The main game loop that continuously checks for player or bot actions, updates the game state,
        and renders the appropriate screen based on the current state.
        """
        while self.running:
            for player in self.game.players:
                if player.won:
                    self.state = "endgame"
                    self.wincol = player.colour
                    player.won = False
                    break

            if self.state == "gamef" and isinstance(
                self.game.players[self.game.currplayer], Bot
            ):
                type, args = self.game.players[self.game.currplayer].make_move()
                if type == "orient":
                    self.clicked_pos = args[0]
                    args = args[1]
            else:
                # print(self.game.players[self.game.currplayer].position," " ,self.game.players[self.game.currplayer].wins, " ",self.game.players[self.game.currplayer].won )
                type, args = self.ui.get()

            match type:
                case "QUIT":
                    self.running = False
                case "MODE":
                    self.game = Game(args, self.ui.screen_rect)
                    self.num_players = args
                    self.state = "botc"
                case "START":
                    if self.state == "botc":
                        self.game.setbots(args)
                        self.state = "gamef"
                case "RESET":
                    self.state = "menu"
                case "move":
                    self.game.make_move("move", args)
                    self.state = "gamef"
                case "wallchoose":
                    self.state = "gamec"
                    if args == self.clicked_pos:
                        self.clicked_pos = None
                        self.state = "gamef"
                    else:
                        self.clicked_pos = args
                case "orient":
                    self.game.make_move("wall", pos=self.clicked_pos, orient=args)
                    self.state = "gamef"
                case "STANDBY":
                    if self.state == "gamec" or self.state == "gamef":
                        self.state = "standby"
                case "endtodelete":
                    self.state = "endgame"

            match self.state:
                case "menu":
                    self.ui.display_menu()
                case "gamef":
                    self.ui.display_game(self.game)
                case "gamec":
                    self.ui.display_orientations(self.game, self.clicked_pos)
                case "endgame":
                    self.ui.display_endgame(self.wincol)
                case "botc":
                    self.ui.choose_bots(self.num_players)
                case "standby":
                    pass

            py.display.flip()
            self.clock.tick(60)

if __name__ == '__main__':
    foo = Quoridor()
    foo.game_loop()
