import curses
import curses.ascii
import re

class curses_pad:
    def __init__(self, win, content='', debug=False):
        self.win = win
        self._cury, self._curx = 0, 0
        self._content = content
        self._topline = 0
        self._lines = content.split('\n')
        self.__debug = debug
        self._update_max_yx()
        self._print_content()
        self._move_curpos()
        win.keypad(1)

    def _update_max_yx(self):
        maxy, maxx = self.win.getmaxyx()
        self._maxy = maxy - 1
        self._maxx = maxx - 1

    def _move_curpos(self):
        self.win.move(self._cury, self._curx)

    def _print_content(self):
        self.win.clear()
        for y in range(self._maxy+1):
            n = self._topline + y
            if n >= len(self._lines): break
            self.win.addstr(y, 0, self._lines[n])
        if self.__debug:
            self.print_endline()
        self.win.refresh()
        self._move_curpos()

    def print_endline(self):
        self.win.addstr(0, self._maxx-5, str(self._end_of_line(self._cury)))

    def edit(self, validate=None):
        while 1:
            ch = self.win.getch()
            if not ch:
                continue
            if not self.do_command(ch):
                break
            self._print_content()
        return '\n'.join(self._lines)

    def do_command(self, ch):
        "Process a single editing command."
        self._update_max_yx()
        (y, x) = self.win.getyx()
        self.lastcmd = ch
        if curses.ascii.isprint(ch):
            n = self._topline + y
            self._lines[n] = self._lines[n][:x] + chr(ch) + self._lines[n][x:]
            # self._move_curpos()
            ## self.win.move(y, x+1)
            self._curx += 1
        elif ch == curses.ascii.SOH:                           # ^a
            ## self.win.move(y, 0)
            self._curx = 0
        elif ch in (curses.ascii.STX,curses.KEY_LEFT, curses.ascii.BS,curses.KEY_BACKSPACE):
            if x > 0:
                ## self.win.move(y, x-1)
                self._curx -= 1
            elif y == 0:
                pass
            else:
                ## self.win.move(y-1, self._maxx)
                self._cury -= 1
                self._curx = self._maxx
            if ch in (curses.ascii.BS, curses.KEY_BACKSPACE):
                self.win.delch()
                if self._lines[y] == '':
                    del(self._lines[y])
                    ## self.win.move(y-1, x)
                    self._cury -= 1
                else:
                    self._lines[y] = self._lines[y][:x-1] + self._lines[y][x:]
        elif ch == curses.ascii.EOT:                           # ^d
            self.win.delch()
        elif ch == curses.ascii.ENQ:                           # ^e
            ## self.win.move(y, self._end_of_line(y))
            self._curx = self._end_of_line(y)
        elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):       # ^f
            if x < self._maxx:
                ## self.win.move(y, x+1)
                self._curx += 1
            elif y == self._maxy:
                pass
            else:
                length = len(self._lines)
                if self._topline + y >= length-1:
                    self._lines.append('')
                ## self.win.move(y+1, 0)
                self._cury += 1
        elif ch == curses.ascii.BEL:                           # ^g
            return 0
        elif ch == curses.ascii.NL:                            # ^j
            if self._maxy == 0:
                return 0
            elif y < self._maxy:
                ## self.win.move(y+1, 0)
                self._cury += 1
        elif ch == curses.ascii.VT:                            # ^k
            if x == 0 and self._end_of_line(y) == 0:
                self.win.deleteln()
            else:
                # first undo the effect of self._end_of_line
                ## self.win.move(y, x)
                self.win.clrtoeol()
        elif ch == curses.ascii.FF:                            # ^l
            self.win.refresh()
        elif ch in (curses.ascii.SO, curses.KEY_DOWN):         # ^n
            length = len(self._lines)
            if self._topline + y >= length-1:
                self._lines.append('')
            if y < self._maxy:
                ## self.win.move(y+1, x)
                self._cury += 1
                if x > self._end_of_line(y+1):
                    ## self.win.move(y+1, self._end_of_line(y+1))
                    self._curx = self._end_of_line(y+1)
        elif ch == curses.ascii.SI:                            # ^o
            self.win.insertln()
        elif ch in (curses.ascii.DLE, curses.KEY_UP):          # ^p
            if y > 0:
                ## self.win.move(y-1, x)
                self._cury -= 1
                if x > self._end_of_line(y-1):
                    ## self.win.move(y-1, self._end_of_line(y-1))
                    self._curx -= self._end_of_line(y-1)
        return 1

    def _end_of_line(self, y):
        self._update_max_yx()
        length = len(curses_pad._invisible_filter(self._lines[y]))
        return length if length - 1 < self._maxx else self._maxx

    @staticmethod
    def _invisible_filter(string):
        return re.sub(r'[\r\n]', '', string)
