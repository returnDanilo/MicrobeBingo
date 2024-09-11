#!/usr/bin/env python3

from os import path, listdir
from string import digits, ascii_letters
from random import shuffle, choices
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageColor

OFFSET = np.array((143, 737))
SQUARE_SIZE = np.array((209,200))
OFFSET2 = np.array((8,8))
GAP = np.array((20,20))
TXT_OFFSET = np.array((134,1844))
FONT = ImageFont.truetype('LondrinaSolid-Regular.ttf', size=27)
COLOR = ImageColor.getrgb('#2c704a')
DIRNAME = "microbe_pics"

images = [Image.open(path.join(DIRNAME, file)) for file in listdir(DIRNAME)]
shuffle(images)

canvas = Image.open("blank_model.png")

labels = ["","","","",""]
i = 0
for y in range(5):
	for x in range(5):
		if (x,y) != (2,2): # skip center square
			canvas.paste(images[i],(OFFSET+OFFSET2+SQUARE_SIZE*(x,y)+(x,y)*GAP).tolist())
			organism_name = path.basename(path.splitext(images[i].filename)[0])
			labels[y] += str(y+1) +"BINGO"[x] +": " +organism_name +"   "

			i+=1

draw = ImageDraw.Draw(canvas)

LENBOARD = 1160 # region to align the text onto
y_text = 0
for line in [x.strip() for x in labels]:
	draw.text(TXT_OFFSET+((LENBOARD -FONT.getsize(line)[0])/2,y_text), line, font=FONT, fill=COLOR)
	y_text += FONT.getsize(line)[1]

card_code = "".join(choices(ascii_letters+digits,k=4))
canvas.save(path.join("/var/www/html/cards", f"{card_code}.png"))
print(card_code)

