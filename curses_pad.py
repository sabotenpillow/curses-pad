import curses
import curses.ascii
import re

class CursesPad:
    def __init__(self, win, content='', debug=False):
        self.win = win
        self._cury, self._curx = 0, 0
        self._content = content
        self._topline = 0
        self._lines = content.split('\n')
        self.__debug = debug
        self._yankbuf = None
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
        self.win.erase()
        for y in range(self._maxy+1):
            n = self._topline + y
            if n >= len(self._lines): break
            self.win.addstr(y, 0, self._lines[n])
        if self.__debug:
            self.__print_endline()
        self.win.refresh()
        self._move_curpos()

    def __print_endline(self):
        self.win.addstr(0, self._maxx-5,
                        str(self._length_of_line(self._cury)))

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
        self.lastcmd = ch
        if curses.ascii.isprint(ch):
            n = self._lines_index()
            self._lines[n] = self._lines[n][:self._curx] \
                             + chr(ch) + self._lines[n][self._curx:]
            self._curx += 1
        elif ch == curses.ascii.SOH:                           # ^a
            self._curx = 0
        elif ch in (curses.ascii.STX,curses.KEY_LEFT):         # ^b
            if self._curx > 0:
                self._curx -= 1
            elif self._cury == 0:
                if self._topline > 0:
                    self._topline -= 1
                    self._curx = self._length_of_line(self._cury)
            else:
                self._cury -= 1
                self._curx  = self._length_of_line(self._cury)
        elif ch in (curses.ascii.BS, curses.KEY_BACKSPACE):  # ^h
            if self._curx > 0:
                self._lines[self._lines_index()] = \
                    self._lines[self._lines_index()][:self._curx-1] \
                    + self._lines[self._lines_index()][self._curx:]
                self._curx -= 1
            elif self._cury == 0:
                if self._topline > 0:
                    x = self._length_of_line(self._cury-1)
                    self._lines[self._lines_index()-1] += self._lines[self._lines_index()]
                    del(self._lines[self._lines_index()])
                    self._topline -= 1
                    self._curx     = x
            else:
                x = self._length_of_line(self._cury-1)
                self._lines[self._lines_index()-1] += self._lines[self._lines_index()]
                del(self._lines[self._lines_index()])
                self._cury -= 1
                self._curx  = x
        elif ch == curses.ascii.EOT:                           # ^d
            if self._curx < self._length_of_line(self._cury):
                self._lines[self._lines_index()] = \
                    self._lines[self._lines_index()][:self._curx] \
                    + self._lines[self._lines_index()][self._curx+1:]
            elif self._lines_index() < len(self._lines) - 1:
                self._lines[self._lines_index()] += self._lines[self._lines_index()+1]
                del(self._lines[self._lines_index()+1])
        elif ch == curses.ascii.ENQ:                           # ^e
            self._curx = self._length_of_line(self._cury)
        elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):       # ^f
            if self._curx < self._length_of_line(self._cury):
                self._curx += 1
            elif self._lines_index() < len(self._lines) - 1:
                if self._cury == self._maxy:
                    self._topline += 1
                else:
                    self._cury += 1
                self._curx  = 0
        elif ch == curses.ascii.BEL:                           # ^g
            return 0
        elif ch == curses.ascii.VT:                            # ^k
            if self._curx < self._length_of_line(self._cury):
                self._yankbuf = self._lines[self._lines_index()][self._curx:]
                self._lines[self._lines_index()] = self._lines[self._lines_index()][:self._curx]
            elif self._lines_index() < len(self._lines) - 1:
                self._lines[self._lines_index()] += self._lines[self._lines_index()+1]
                del(self._lines[self._lines_index()+1])
        elif ch == curses.ascii.FF:                            # ^l
            self.win.refresh()
        elif ch in (curses.ascii.SO, curses.KEY_DOWN):         # ^n
            if self._lines_index() < len(self._lines) - 1:
                if self._curx > self._length_of_line(self._cury+1):
                    self._curx = self._length_of_line(self._cury+1)
                if self._cury < self._maxy:
                    self._cury += 1
                elif self._cury == self._maxy:
                    self._topline += 1
        elif ch == curses.ascii.SI:                            # ^o
            self._lines.insert(self._lines_index()+1, '')
            self._cury += 1
            self._curx  = 0
        #elif ch == curses.ascii.CR:                            # ^m
        elif ch == curses.ascii.NL:                            # ^j
            index = self._lines_index()
            self._lines.insert(index+1, self._lines[index][self._curx:])
            self._lines[index] = self._lines[index][:self._curx]
            if self._cury == self._maxy:
                self._topline += 1
            else:
                self._cury += 1
            self._curx  = 0
        elif ch in (curses.ascii.DLE, curses.KEY_UP):          # ^p
            if self._cury > 0:
                self._cury -= 1
                if self._curx > self._length_of_line(self._cury):
                    self._curx = self._length_of_line(self._cury)
            elif self._cury == 0 and self._topline > 0:
                self._topline -= 1
                if self._curx > self._length_of_line(0):
                    self._curx = self._length_of_line(0)
        elif ch == curses.ascii.NAK:                           # ^u
            if self._curx > 0:
                self._yankbuf = self._lines[self._lines_index()][:self._curx]
                self._lines[self._lines_index()] = self._lines[self._lines_index()][self._curx:]
                self._curx = 0
            elif self._cury == 0:
                if self._topline > 0:
                    x = self._length_of_line(self._cury-1)
                    self._lines[self._lines_index()-1] += self._lines[self._lines_index()]
                    del(self._lines[self._lines_index()])
                    self._topline -= 1
                    self._curx     = x
            else:
                x = self._length_of_line(self._cury-1)
                self._lines[self._lines_index()-1] += self._lines[self._lines_index()]
                del(self._lines[self._lines_index()])
                self._cury -= 1
                self._curx  = x
        elif ch == curses.ascii.EM and self._yankbuf != None: # ^y
            n = self._lines_index()
            self._lines[n] = self._lines[n][:self._curx] \
                             + self._yankbuf + self._lines[n][self._curx:]
            self._curx += len(self._yankbuf)
        return 1

    def _length_of_line(self, y):
        self._update_max_yx()
        length = len(CursesPad._invisible_filter(self._lines[self._topline + y]))
        return length if length - 1 < self._maxx else self._maxx

    def _lines_index(self):
        return self._topline + self._cury

    @staticmethod
    def _invisible_filter(string):
        return re.sub(r'[\r\n]', '', string)
