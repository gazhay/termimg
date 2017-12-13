#!/usr/bin/env python3

from PIL import Image
import argparse,math
import shutil,warnings

#convert magick:wizard -colorspace Gray -colors 2 colorspace-gray-colors-2.bmp

parser = argparse.ArgumentParser()
parser.add_argument('file')
parser.add_argument('-x' , "--xzoom",  action="store"      , dest="xoff", type=int,  default=0, help="Zoom Offset X")
parser.add_argument('-y' , "--yzoom",  action="store"      , dest="yoff", type=int,  default=0, help="Zoom Offset Y")
parser.add_argument('-b' , "--box",    action="store_true" , dest="boxm", default=False, help="Restrict Rows")
parser.add_argument('-i' , "--scan",   action="store_true" , dest="intr", default=False, help="Interactive Mode")
parser.add_argument('-t' , "--true",   action="store_false", dest="tcol", default=True , help="Turn off terminal true colour mode")
parser.add_argument('-s' , "--squish", action="store_false", dest="sqsh", default=True , help="Use unicode half blocks to reduce size")
parser.add_argument('-w' , "--width",  action="store"      , dest="widt", type=int,  default=0, help="Width for pipers")
parser.add_argument('-1' , "--braile", action="store_true" , dest="bawb", default=False, help="We need a 1bit repr in braille")
parser.add_argument('-p' , "--patana", action="store_true" , dest="pata", default=False, help="Patana mode")
parser.add_argument('-d' , "--debug" , action="store_true" , dest="debg", default=False, help="Save intermediate docs")
parser.add_argument('--version', action='version', version='%(prog)s 1.0')
warnings.simplefilter('ignore', Image.DecompressionBombWarning)
opts          = parser.parse_args()
try:
	im            = Image.open(opts.file).convert('RGBA')      # Open a file, convert it to RGBA if possible
except:
	print("Could not open file "+opts.file)
	exit(1)
	
mysize        = shutil.get_terminal_size((80, 20))         # Terminal falls back to 80x20
if opts.widt>0:
    cols      = opts.widt
else:
    cols      = mysize.columns  
maxrows       = mysize.lines
maxcols       = cols
width, height = im.size
new_width     = cols
new_height    = int(new_width * height / width)

if width<cols:
    # Don't scale up - it be fugly
    # opts.intr  = True
    new_width  = width 
    new_height = height

im.load()
tempim         = Image.new("RGB", im.size, (255, 255, 255)) # Convert the image to RGB dropping alpha for white
tempim.paste(im, mask=im.split()[3])                       # drop 4th[3] channel
if opts.bawb or opts.pata:
    new_width  = (cols * 2)
    heightscale = 2 if opts.pata else 1
    new_height = int((new_width * height / width)/ heightscale)
    if width<cols:
        new_width  = width  * 2
        new_height = height * 2

im             = tempim                                     # temp replaces real
if (opts.intr):
    pass                                                   # don't resize on keyboard mode
else:
    if width!=new_width:
        im = im.resize((new_width, new_height), Image.ANTIALIAS)
        if opts.bawb or opts.pata:
            im = im.convert('1',dither=Image.FLOYDSTEINBERG) # For dithering to B&W

if not opts.tcol:
  im = im.convert('P', palette=Image.WEB)      # If we are in dithermode
  if opts.debg:
    im.save("debug.png")
  im = im.convert("RGB")                       # Just cheat and convert it back

pixel_values = list(im.getdata())

doc  = []
data = []

def rgb2ansi(rgb):
    # Converts RGB value to ANSI256 palette
    if (opts.tcol):
        return rgb
    else:
       r = rgb[0]
       g = rgb[1]
       b = rgb[2]
       retval = 16 \
              + (36 * int(round(r / 255 * 5))) \
              + (6  * int(round(g / 255 * 5))) \
              +       int(round(b / 255 * 5))
    return retval

def int2ansi(i, fore=True):
    # Converts Color to ANSI color string
    if fore:
        num=48
    else:
        num=38
    if opts.tcol:
        return '\033[%d;2;%d;%d;%dm'%(num,i[0],i[1],i[2])
    else: 
        return '\033[%d;5;%dm'%(num,i)

def scrollbar(wherex,wherey,xbar=False,ybar=False):
    if ybar:
        xval=maxcols+1
        theline=max(1,int((wherey/im.size[1])*maxrows))
        for row in range(0,maxrows):
            if row==theline:
                char="\033[40m \033[0m"
            else:
                char="\033[47m \033[0m"
            print("\033[%d;%df%s"%(row,xval,char),end='')
    if xbar:
        yval=maxrows+1
        theline=max(1,int((wherex/im.size[0])*maxcols))
        for row in range(0,maxcols):
            if row==theline:
                char="\033[40m \033[0m"
            else:
                char="\033[47m \033[0m"
            print("\033[%d;%df%s"%(yval,row,char),end='')

def pattern2ascii(inpat):
    pixels  = ((0x01, 0x08),(0x02, 0x10),(0x04, 0x20),(0x40, 0x80))
    outChar = 0x2800
    for yp in range(0,3):
        for xp in range(0,1):
            if (inpat[yp][xp]==0):
                outChar |= pixels[yp][xp]
    return chr(outChar)

def patana2ascii(inpat):
  ((a,b),(c,d))=inpat
  patts={
    "0000" : 0x20,
    "0001" : 0x259D,
    "0010" : 0x2596,
    "0011" : 0x2584,
    "0100" : 0x259D,
    "0101" : 0x2590,
    "0110" : 0x259E,
    "0111" : 0x259F,
    "1000" : 0x2598,
    "1001" : 0x259A,
    "1010" : 0x258C,
    "1011" : 0x2599,
    "1100" : 0x2580,
    "1101" : 0x259C,
    "1110" : 0x259B,
    "1111" : 0x2588
    }
  return chr(patts[(str(a)+str(b)+str(c)+str(d))])

if (opts.intr):
# Interactive mode
# reset terminal to 0,0
# draw zoom 1, 0,0
# allow keyboard input, arrows or wasd, and move +cols/2 or -lines/2
# repetez vous
  controlfuse=False
  def getchar():
      global controlfuse
      #Returns a single character from standard input
      import tty, termios, sys
      fd = sys.stdin.fileno()
      old_settings = termios.tcgetattr(fd)
      try:
         tty.setraw(sys.stdin.fileno())
         ch = sys.stdin.read(1)
      finally:
         termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
      #print("You pressed : "+ch)
      if controlfuse:
         controlfuse=False
         if ch=='A': return 'w'
         if ch=='B': return 's'
         if ch=='C': return 'd'
         if ch=='D': return 'a'
      if ch=='[':
         controlfuse=True
      return ch

  key     = ''
  xoff    = 0
  yoff    = 0
  zoom    = 1
  boxm    = True
  maxcols = maxcols
  maxrows = maxrows
  xfactor = int(maxcols/2)
  yfactor = int(maxrows/2)
#left arrow: 37 up arrow: 38 right arrow: 39 down arrow: 40
  needRedraw=True
  while key != 'q':
    if key == 'a' or key == chr(37):
       xoff = max(0, xoff - xfactor)
       needRedraw=True
    elif key == 'd' or key == chr(39):
       xoff = min(width-maxcols, xoff + xfactor)
       needRedraw=True
    elif key == 'w' or key == chr(38):
       yoff = max(0, yoff - yfactor)
       needRedraw=True
    elif key == 's' or key == chr(40):
       yoff = min(height-maxrows, yoff + yfactor)
       needRedraw=True
    elif key == 'r':
       needRedraw=True

    if needRedraw:
       print("\033[0;0f", end="") # Reset cursor
       for y in range(yoff,(yoff+maxrows)):
          for x in range(xoff,(xoff+maxcols)):
              thiscolor = im.getpixel((x,y))
              print(int2ansi(rgb2ansi(thiscolor)), end='')
              print(" ",end='')
          print('\033[0m',end='') # Reset colors
       needRedraw=False
       # print("%d %d" % (xoff,yoff))
    key = getchar()

else:
    if opts.bawb:
        # Braille Mode
        steppy = 4               # One line at a time
        for y in range(0,int(new_height), steppy):
            for x in range(0,int(new_width), 2):
                thispattern=[[0,0],[0,0],[0,0],[0,0]]
                for yp in range(0,4):
                    for xp in range(0,2):
                        try:
                            thispattern[yp][xp]=im.getpixel((x+xp,y+yp))
                        except:
                            thispattern[yp][xp]=0
                print(pattern2ascii(thispattern), end="")
            print("")
    elif opts.pata:
        for y in range(0,int(new_height), 2):
            for x in range(0,int(new_width), 2):
                thispattern=[[0,0],[0,0]]
                for yp in range(0,2):
                    for xp in range(0,2):
                        try:
                            thispattern[yp][xp]=0 if (im.getpixel((x+xp,y+yp))>1) else 1
                        except:
                          thispattern[yp][xp]=1
                print(patana2ascii(thispattern), end="")
            print("")
    else:
        # Non-interactive mode
        steppy = 1               # One line at a time
        if opts.sqsh: steppy = 2 # Unicode squishy mode, step 2 lines at a time
        for y in range(0,int(new_height), steppy):
            for x in range(0,int(new_width)):
                if opts.sqsh:
                    # Squish mode, get 2 colors, fore top half, back lower
                    forecolor = int2ansi(rgb2ansi(im.getpixel((x,y)) ), fore=False)
                    try:
                        backcolor = int2ansi(rgb2ansi(im.getpixel((x,y+1))))
                    except:
                        # most likely an odd number of lines, use white
                        backcolor = int2ansi(rgb2ansi( (255,255,255) ))
                    print(forecolor+backcolor, end='')
                    print(u"\u2580",end='')
                else:
                    thiscolor = int2ansi(rgb2ansi(im.getpixel((x,y))))
                    print(thiscolor,end='')
                    print(" ",end='')
            print('\033[0m')


