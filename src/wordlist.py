from PIL import ImageGrab, ImageEnhance
import pytesseract
import time
import mouse


def movenclick(posx, posy, click="left"):
    mouse.move(posx, posy, absolute=True, duration=0)
    mouse.click(click)
    return None


class WordBlitz:
    def __init__(self, fn, bbox_partie, bbox_game, bbox_ad, bbox_res, bbox_allwords):
        self.fn = fn
        self.bbox_partie = bbox_partie
        self.bbox_game = bbox_game
        self.bbox_ad = bbox_ad
        self.bbox_res = bbox_res
        self.bbox_allwords = bbox_allwords
        if not (self.islaunched()):
            raise Exception("Word Blitz not launched")

    def islaunched(self):
        bounding_box = ImageGrab.grab(bbox=self.bbox_partie, all_screens=True)
        str = pytesseract.image_to_string(bounding_box)
        return "Partie" in str

    def poscloseget(self):
        bounding_box = ImageGrab.grab(bbox=self.bbox_ad, all_screens=True)
        data = pytesseract.image_to_data(bounding_box, output_type="dict")
        name_l = [name.lower() for name in data["text"]]
        posclose = None
        if "fermer" in name_l:
            idx = name_l.index("fermer")
            posclose = (
                data["left"][idx] + self.bbox_ad[0],
                data["top"][idx] + self.bbox_ad[1],
            )
        return posclose

    def wordlistget(self):
        old_imgbox = None
        mouse.move(620, -420, absolute=True, duration=0)
        imgbox = ImageGrab.grab(bbox=self.bbox_res, all_screens=True)
        wordlist = []
        nloop = 0
        while imgbox != old_imgbox:
            old_imgbox = imgbox
            enhancer = ImageEnhance.Contrast(imgbox)
            imgbox_enh = enhancer.enhance(20)
            data = pytesseract.image_to_data(imgbox_enh, output_type="dict")
            wordlist_box = [
                word
                for word in data["text"]
                if word != ""
                if word != " "
                if word.isalpha()
                if word == word.upper()
                if not (word in wordlist)
            ]
            wordlist += wordlist_box
            mouse.wheel(-2)
            time.sleep(0.1)
            nloop += 1
            if nloop > 400:
                print("wordlistget too much words scroll")
                break
            mouse.move(620, -420, absolute=True, duration=0)
            imgbox = ImageGrab.grab(bbox=self.bbox_res, all_screens=True)
        return wordlist

    def wordlistupd(self):
        imgbox = ImageGrab.grab(bbox=self.bbox_allwords, all_screens=True)
        str = pytesseract.image_to_string(imgbox)
        if not ("TOUS LES MOTS" in str):
            raise Exception("Result page not in position")
        movenclick(760, -650)
        time.sleep(0.5)
        wordlist = self.wordlistget()
        with open(self.fn, "a") as file:
            file.write("|".join(wordlist) + "\n")

    def startgame(self, randomone=True):
        if not (self.islaunched()):
            raise Exception("Word Blitz not launched")
        if randomone:
            movenclick(760, -450)
        else:
            movenclick(700, -250)
            time.sleep(0.5)
            movenclick(700, -120)
        time.sleep(5)

    def finishgame(self):
        movenclick(460, -835)
        time.sleep(1)
        movenclick(620, -400)
        time.sleep(10)
        # close ad
        posclose = self.poscloseget()
        if not (posclose is None):
            movenclick(posclose[0], posclose[1])
        else:
            print("posclose is None")
            movenclick(1075, -150)
            time.sleep(0.5)
            movenclick(455, -830)
            time.sleep(0.5)
            movenclick(45, -860)
            time.sleep(0.5)
            movenclick(850, -805)
        time.sleep(1)
        movenclick(865, -820)
        time.sleep(0.5)
        movenclick(860, -830)
        time.sleep(0.5)
        movenclick(850, -805)
        time.sleep(0.5)

    def wordlistexit(self):
        time.sleep(0.5)
        movenclick(650, -125)  # continuer
        time.sleep(0.5)
        movenclick(460, -830)  # back to home page

    def cleangame(self):
        time.sleep(0.5)
        movenclick(620, -250)
        time.sleep(0.5)
        movenclick(680, -120)
        time.sleep(1)
        movenclick(450, -830)
        time.sleep(1)
        movenclick(450, -830)
        time.sleep(1)
        movenclick(450, -830)


def wordblitz(nloopmax=10, randomone=True, clean=False):
    bbox_partie = (650, -500 + 40, 850, -400 + 40)
    bbox_game = (400, -900, 900, -50)
    bbox_ad = (20, -900, 1300, -50)
    bbox_res = (660, -575, 900, -225)
    bbox_allwords = (660, -675, 855, -635)
    wb = WordBlitz("wordlist.txt", bbox_partie, bbox_game, bbox_ad, bbox_res, bbox_allwords)
    nloop = 1
    while nloop <= nloopmax:
        if clean:
            wb.cleangame()
        else:
            wb.startgame(randomone=randomone)
            wb.finishgame()
            wb.wordlistupd()
            wb.wordlistexit()
        print(nloop, "/", nloopmax)
        nloop += 1
        time.sleep(2)
