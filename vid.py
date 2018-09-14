#!/usr/bin/python3 

try:
    from PIL import Image
except:
    print("Please install PILlow python modules.")
import shutil
try:
    import cv2
except:
    print("cv2 module not found. Usually apt install python3-opencv will rectify")

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('file')
opts   = parser.parse_args()

# filemn = "mario.png"

mysize                = shutil.get_terminal_size((80, 20))         # Terminal falls back to 80x20
def int2ansi(i, fore=True):
    # Converts Color to ANSI color string
    if fore:
        num=48
    else:
        num=38
    return '\033[%d;2;%d;%d;%dm'%(num,i[0],i[1],i[2])

def frame2ascii(inimg):
    xbound,ybound = inimg.size
    for y in range(0, ybound, 2):
        for x in range(0,xbound):
            backcolor = int2ansi(inimg.getpixel( (x,y  )), fore=False)
            try:
                forecolor = int2ansi(inimg.getpixel( (x,y+1))        )
            except:
                forecolor = int2ansi( (255,255,255) )
            print(forecolor+backcolor+u"\u2580", end='')
        print('\033[0m')
    print('\033[0;0H')

# frame2ascii(im)
try:
    vidcap = cv2.VideoCapture(opts.file)
except:
    print("Could not open file {}".format(opts.file))
    exit(1)
success,image = vidcap.read()
origheight, origwidth = image.shape[:2]
new_width             = mysize.columns
new_height            = int(new_width * origheight / origwidth)
count = 0
# framewid, framehei = (0,0)
print('\033[0;0H')
try:
    while success:
        cv2_im = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        pil_im = Image.fromarray(cv2_im).resize( (new_width,new_height) ).convert('RGB')
        # cv2.imwrite("frame%d.jpg" % count, image)     # save frame as JPEG file      
        framewid, framehei = pil_im.size
        # pil_im.show()
        frame2ascii(pil_im)
        success,image = vidcap.read()
        # print('Read a new frame: ', success)
        count += 1
        # if count>1:
        #     raise ValueError("Early break")
except:
    print('\033[0m\033[2J')
    print("Frames = {}".format(count))
    # print("Was it a success {}".format(success))
    # print("I rendered at {},{}".format(new_width,new_height))
    # print("Last frame rendered was {},{}".format(framewid,framehei))