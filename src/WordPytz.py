import common
import mouse
import screeninfo
from PIL import ImageGrab, ImageOps
import pytesseract
import numpy as np
import time
import os


class WordPytz:
    def __init__(self):
        self._monitor_init()
        if self.monitor is None:
            raise Exception("Word Blitz not launched")
        self._bbox_wb_init()
        self.gridsize = 4
        self._prop_init()
        self._lettergridpx_init()
        self._lettergridpxabs_init()
        self._letterboxpx_init()
        self._bbox_letterpx_init()
        self._movegrid_init()
        self.wordlist = self.wordlist_get()

    def _monitor_init(self):
        wbopen = False
        monitor_l = screeninfo.get_monitors()
        for monitor in monitor_l:
            bbox = [
                monitor.x,
                monitor.y,
                monitor.x + monitor.width,
                monitor.y + monitor.height,
            ]
            img = ImageGrab.grab(bbox=bbox, all_screens=True)
            imgdata = pytesseract.image_to_data(ImageOps.invert(img), output_type="dict")
            if all([txt in imgdata["text"] for txt in ["Word", "Blitz"]]):
                wbopen = True
                break
        if not (wbopen):
            monitor = None
        self.monitor = monitor

    def _bbox_wb_init(self):
        monitor = self.monitor
        bbox = [monitor.x, monitor.y, monitor.x + monitor.width, monitor.y + monitor.height]
        img = ImageGrab.grab(bbox=bbox, all_screens=True)
        img_arr = np.array(img)
        # x0 + x1
        imgrow = img_arr[int(len(img_arr[0]) / 2)]
        emptyarea = np.where(np.all(imgrow == np.array([24, 25, 26]), axis=1))[0]
        idx = np.where(np.diff(emptyarea) > 1)[0][0]
        bbox_wbx0 = bbox[0] + emptyarea[idx] + 1
        bbox_wbx1 = bbox[0] + emptyarea[idx + 1] - 1
        # y0
        imgcol = img_arr[:, int(len(img_arr[0]) / 2)]
        emptyarea = np.where(np.all(imgcol == np.array([24, 25, 26]), axis=1))[0]
        bbox_wby0 = bbox[1] + emptyarea[-1] + 1
        # y1
        imgcol = img_arr[:, int(len(img_arr[0]) / 10)]
        emptyarea = np.where(np.all(imgcol == np.array([24, 25, 26]), axis=1))[0]
        bbox_wby1 = bbox[1] + emptyarea[-1]
        self.bbox_wb = [bbox_wbx0, bbox_wby0, bbox_wbx1, bbox_wby1]

    def _prop_init(self):
        self.prop = {
            "newrandom": [0.7, 0.55],
            "letter0": [0.158, 0.4065],
            "letteroffs": [0.229, 0.13],
            "letterbox": [0.075, 0.0584],
        }

    def _lettergridpx_init(self):
        letter0 = self.prop["letter0"]
        letteroffs = self.prop["letteroffs"]
        width = self.bbox_wb[2] - self.bbox_wb[0]
        height = self.bbox_wb[3] - self.bbox_wb[1]
        self.lettergridpx = [
            [
                [
                    int((letter0[0] + letteroffs[0] * col) * width),
                    int((letter0[1] + letteroffs[1] * row) * height),
                ]
                for row in range(self.gridsize)
            ]
            for col in range(self.gridsize)
        ]

    def _lettergridpxabs_init(self):
        self.lettergridpxabs = [
            [
                [
                    self.lettergridpx[row][col][0] + self.bbox_wb[0],
                    self.lettergridpx[row][col][1] + self.bbox_wb[1],
                ]
                for row in range(self.gridsize)
            ]
            for col in range(self.gridsize)
        ]

    def _letterboxpx_init(self):
        width = self.bbox_wb[2] - self.bbox_wb[0]
        height = self.bbox_wb[3] - self.bbox_wb[1]
        letterbox = self.prop["letterbox"]
        self.letterboxpx = [int(width * letterbox[0]), int(height * letterbox[1])]

    def _bbox_letterpx_init(self):
        lettergridpx = self.lettergridpx
        letterboxpx = self.letterboxpx
        self.bbox_letterpx = [
            [
                [
                    int(lettergridpx[row][col][0] - letterboxpx[0] / 2),
                    int(lettergridpx[row][col][1] - letterboxpx[1] / 2),
                    int(lettergridpx[row][col][0] + letterboxpx[0] / 2),
                    int(lettergridpx[row][col][1] + letterboxpx[1] / 2),
                ]
                for row in range(self.gridsize)
            ]
            for col in range(self.gridsize)
        ]

    def _movegrid_init(self):
        move = {
            "L": (0, -1),
            "DL": (1, -1),
            "D": (1, 0),
            "DR": (1, 1),
            "R": (0, 1),
            "UR": (-1, 1),
            "U": (-1, 0),
            "UL": (-1, -1),
        }
        cellmove = {
            "LDRU": [
                move["L"],
                move["DL"],
                move["D"],
                move["DR"],
                move["R"],
                move["UR"],
                move["U"],
                move["UL"],
            ],
            "LDR": [move["L"], move["DL"], move["D"], move["DR"], move["R"]],
            "DRU": [move["D"], move["DR"], move["R"], move["UR"], move["U"]],
            "LRU": [move["L"], move["R"], move["UR"], move["U"], move["UL"]],
            "LDU": [move["L"], move["DL"], move["D"], move["U"], move["UL"]],
            "DR": [move["D"], move["DR"], move["R"]],
            "RU": [move["R"], move["UR"], move["U"]],
            "LU": [move["L"], move["UL"], move["U"]],
            "LD": [move["D"], move["DL"], move["L"]],
        }
        self.movegrid = [
            [cellmove["DR"], cellmove["LDR"], cellmove["LDR"], cellmove["LD"]],
            [cellmove["DRU"], cellmove["LDRU"], cellmove["LDRU"], cellmove["LDU"]],
            [cellmove["DRU"], cellmove["LDRU"], cellmove["LDRU"], cellmove["LDU"]],
            [cellmove["RU"], cellmove["LRU"], cellmove["LRU"], cellmove["LU"]],
        ]

    def wordlist_get(self):
        fn = f"{common.dirout}/wordlist.txt"
        if not (os.path.isfile(fn)):
            raise Exception(f"{fn} missing. Dictionnary must be retrieved")
        wordlist = []
        with open(fn) as file:
            line_l = file.readlines()
            for line in line_l:
                wordlist += [txt for txt in line.rstrip().split("|")]
            wordlist = np.unique(wordlist)
        wordlist = wordlist.tolist()
        wordlist = sorted(wordlist, key=len)
        return wordlist

    def lettergrid_get(self, img):
        config1 = "--psm 10 -c tessedit_char_whitelist='ABCDEFGHIJKLMNOPQRSTUVWXYZ'"
        config2 = "--psm 8 -c tessedit_char_whitelist='ABCDEFGHIJKLMNOPQRSTUVWXYZ'"
        lettergrid = [
            [None for row in range(self.gridsize)] for col in range(self.gridsize)
        ]
        for row in range(self.gridsize):
            for col in range(self.gridsize):
                bbox = self.bbox_letterpx[row][col]
                imgletter = img.crop(bbox)
                letter = pytesseract.image_to_string(imgletter, config=config1)
                letter = letter.replace("\n", "").replace("\x0c", "")
                if len(letter) == 0:
                    letter = pytesseract.image_to_string(imgletter, config=config2)
                    letter = letter.replace("\n", "").replace("\x0c", "")
                    if len(letter) == 0:
                        print(f"WARNING: letter not found in row={row}, col={col}")
                lettergrid[row][col] = letter
        return lettergrid

    def word_l_filter(self, word_l, lettergrid, filtering):
        if filtering == "oneletter":
            letter_l = np.unique(
                [
                    lettergrid[row][col]
                    for row in range(self.gridsize)
                    for col in range(self.gridsize)
                ]
            ).tolist()
            filtword_l = []
            for word in word_l:
                ok = True
                for letter in word:
                    if not (letter in letter_l):
                        ok = False
                        break
                if ok:
                    filtword_l += [word]
        else:
            raise Exception(f"Invalid filtering={filtering}")
        return filtword_l

    def cellpath_l_get(self, lettergrid, nextpos, word, cellpath, cellpath_l=[]):
        row = cellpath[-1][0]
        col = cellpath[-1][1]
        lenword = len(word)
        if nextpos >= lenword:
            return []
        if nextpos == 1:
            cellpath_l = []
        cellmove = self.movegrid[row][col]
        letter = word[nextpos]
        cellpath_cp = cellpath.copy()
        for move in cellmove:
            cellpath = cellpath_cp.copy()
            nextrow = row + move[0]
            nextcol = col + move[1]
            if (nextrow, nextcol) in cellpath:
                continue
            if letter == lettergrid[nextrow][nextcol]:
                cellpath += [(nextrow, nextcol)]
                if nextpos == len(word) - 1:
                    cellpath_l += [cellpath]
                else:
                    self.cellpath_l_get(lettergrid, nextpos + 1, word, cellpath, cellpath_l)
        return cellpath_l

    def allcellpath_l_get(self, word, lettergrid):
        cell_l = [
            (row, col)
            for row in range(self.gridsize)
            for col in range(self.gridsize)
            if word[0] == lettergrid[row][col]
        ]
        allcellpath_l = []
        for cell in cell_l:
            row = cell[0]
            col = cell[1]
            allcellpath_l += self.cellpath_l_get(lettergrid, 1, word, [(row, col)])
        return allcellpath_l

    def bestcellpath_info_get(self, word, lettergrid):
        cellpath_l = self.allcellpath_l_get(word, lettergrid)
        # TODO: weight on letter bonus and word score
        score = 0
        cellpath = cellpath_l[0] if len(cellpath_l) > 0 else None
        return cellpath, score

    def bestcellpath_info_dct_get(self, word_l, lettergrid):
        bestcellpath_info_dct = {}
        for word in word_l:
            bestcellpath_info = self.bestcellpath_info_get(word, lettergrid)
            if not (bestcellpath_info[0] is None):
                bestcellpath_info_dct[word] = bestcellpath_info
        return bestcellpath_info_dct

    def cellpath_draw(self, cellpath):
        pos = self.lettergridpxabs[cellpath[0][0]][cellpath[0][1]]
        mouse.move(pos[0], pos[1])
        time.sleep(0.015)
        mouse.click(button="left")
        time.sleep(0.015)
        mouse.press(button="left")
        for idx in range(1, len(cellpath)):
            pos = self.lettergridpxabs[cellpath[idx][0]][cellpath[idx][1]]
            mouse.move(pos[0], pos[1], duration=0.015)
        mouse.release(button="left")
        return None

    def gamebot(self):
        img = ImageGrab.grab(bbox=self.bbox_wb, all_screens=True)
        lettergrid = self.lettergrid_get(img)
        word_l = self.word_l_filter(self.wordlist, lettergrid, "oneletter")
        bestcellpath_info_dct = self.bestcellpath_info_dct_get(word_l, lettergrid)
        bestcellpath_info_l = sorted(bestcellpath_info_dct.values(), key=lambda val: val[1])
        bestcellpath_l = [val[0] for val in bestcellpath_info_l]
        for cellpath in bestcellpath_l:
            self.cellpath_draw(cellpath)
        return None


# example:
# wb = WordPytz()
# wb.gamebot()
