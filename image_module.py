import os
import math
from PIL import Image
import ImageFont, ImageDraw
import settings
import re

# image resize bug workaround!
import ImageFile
ImageFile.MAXBLOCK = 1000000 # default is 64k

import sift_turbo

def video_to_frames(video,fps):
    if settings.is_win:
        cmd = "video_to_frames.bat " + str(video) + " " + fps
    else:
        cmd = "./video_to_frames.sh " + str(video) + " " + fps
    try:
        os.system(cmd)
        print 'processing', video, 'finished\n'        
    except:
        print 'Error in processing video'
        exit(-1)        
        
def frames_to_video(video,fps):
    if settings.is_win:
        cmd = "frames_to_video.bat " + fps + " " + str(video)
    else:
        cmd = "./frames_to_video.sh " + fps + " " + str(video)
    try:
        os.system(cmd)
        print 'processing', video, 'finished\n'
    except:
        print 'Error in processing video'
        exit(-1)        

def draw_text_on_img(img, text, right=False, mult=False,color_text=(255,255,255),color_box=(0,0,250),font=("arial.ttf", 12)):

    im = Image.open(img)
    file, ext = os.path.splitext(img)
    draw = ImageDraw.Draw(im)
    
    font_font, font_size = font[0], font[1]
    font = ImageFont.truetype(font_font,font_size)
    
    border = 10
    box_width = 75
    box_height = 20
    width, height = im.size
    if right:
        if mult:
            box_width += 5 + mult*17
        draw.rectangle((width-border-box_width, height-border-box_height, width-border, height-border), fill=color_box)
        draw.text((width-border-box_width+5,height-border-box_height+4),'%s' % (text), fill=color_text, font=font)
    else:
        draw.rectangle((border, border, border+box_width, border+box_height), fill=color_box)
        draw.text((border+5,border+4),'%s' % (text), fill=color_text, font=font)
    im.save(img,"JPEG")
    # im.show()

def remove_file_img(img):
    if os.path.exists(img.filename):
        os.remove(img.filename)
    
def remove_temp_files_img(img):
    if img.filename_resized and os.path.exists(img.filename_resized):
        os.remove(img.filename_resized)
        img.filename_resized = None
    if img.filename_pgm and os.path.exists(img.filename_pgm):
        os.remove(img.filename_pgm)
        img.filename_pgm = None
    if img.filename_keypoints and os.path.exists(img.filename_keypoints):
        os.remove(img.filename_keypoints)
        img.filename_keypoints = None

def remove_temp_files_clusters(clusters, verbose):
    # temp fileok torlese
    if verbose:print '\nDeleting temporary files...'
    for cluster in clusters:
        for img in cluster:
            remove_temp_files_img(img)
    if verbose:print 'Deleting temporary files done'

def prepare_img_for_sift(img):
    if not (img.filename_resized and os.path.exists(img.filename_resized)):
        img.filename_resized = resize_image(img, settings.THUMBS_SIZE)
    if not (img.filename_pgm and os.path.exists(img.filename_pgm)):
        img = convert_to_pgm(img)
    if not (img.filename_keypoints and os.path.exists(img.filename_keypoints)):
        img = sift_turbo.make_keypoints(img)
    loc, desc = sift_turbo.get_descriptors(img)
    img.loc = loc
    img.desc = desc
    return img

class Object():
    attributes = {}
    
    def __init__(self):
        self.attributes = {}
    
    def get_distance(self,other,from_object=False):
        # distance = sqrt(((P1-Q1)^2 + (P1-Q1)^2 + ... + (Pn-Qn)^2)/n)
        if from_object: other = other.attributes
        s=0
        n=0
        for (k,a1) in self.attributes.items():
            if other.get(k):
                n+=1
                a2 = other.get(k)
                d=(a1.compare(a2))**2
                d*=a1.weight
                s+=d
        # ha nincsenek attributumai a 'self' kepnek, az 'other'-tol valo tavja legyen vegtelen
        if n==0: return Decimal('Infinity')
        else: return math.sqrt(s/n)        

class ImageObject(Object):
    filename=''
    filename_resized=None
    filename_pgm=None
    filename_keypoints=None
    loc = None
    desc = None
    matched = None
    was_matched_with = []
    matching_qom = None
    is_result = False
    # clusternum here means 0-based
    flag_move_from_clusternum = None
    flag_move_to_clusternum = None
    sceneNum = None
    
    def __repr__(self):
        return repr(self.filename)
    
    def __init__(self, filename):
        Object.__init__(self)
        self.filename = filename
        self.filename_resized=None
        self.filename_pgm=None
        self.filename_keypoints=None
        self.loc = None
        self.desc = None
        self.matched = None
        self.was_matched_with = []
        self.matching_qom = None
        self.is_result = False
        self.flag_move_from_clusternum = None
        self.flag_move_to_clusternum = None
        sceneNum = None
        
    def get_only_filename(self):
        return str(self.filename.split(settings.GLOBAL_SLASH)[-1])
    def get_only_num(self):
        try:
            return int(self.get_only_filename().lstrip('img').lstrip('0').rstrip('.jpg'))
        except:
            num = self.get_only_filename()
            num = re.sub('\.\w*$', '', num)
            num = re.sub('^\D*', '', num).lstrip('0')

def resize_image(image, size='400x300'):
    x, y = [int(x) for x in size.split('x')]
    file = Image.open(image.filename)
    only_filename = image.get_only_filename()
    filehead, filetail = os.path.split(image.filename)
    
    basename, format = os.path.splitext(filetail)
    miniature = basename + '_' + size + format            
    
    
    if filehead: filename = filehead + settings.GLOBAL_SLASH + filetail
    else: filename = filetail
    miniature_filename = os.path.join(filehead, miniature)

    if os.path.exists(miniature_filename) and os.path.getmtime(filename)>os.path.getmtime(miniature_filename):
        try:
            os.unlink(miniature_filename)
        except:
            return ""

    # if the image wasn't already resized, resize it
    if not os.path.exists(miniature_filename):        
        try:
            image = Image.open(filename)
        except:
            return ""

        w,h=image.size
        if x==0: x=int(float(y)*float(w)/float(h))
        if y==0: y=int(float(x)*float(h)/float(w))

        # The filter argument can be one of NEAREST, BILINEAR, BICUBIC, or ANTIALIAS (best quality). If omitted, it defaults to NEAREST.
        image.thumbnail((x, y),Image.ANTIALIAS)
        try:
            if image.format.lower() in ("gif","png"):
                image.save(miniature_filename, image.format, quality=90)
            else:
                image.save(miniature_filename, image.format, quality=90, optimize=1)
        except:
            try:
                image.save(miniature_filename, image.format, quality=90)
            except:
                return ""
    
    print 'Resizing', only_filename, 'complete!'
    return miniature_filename

def convert_to_pgm(img):
    if img.filename_resized: 
        img_name = img.filename_resized
    else: 
        img_name = img.filename
    basename = img_name.split('.')[-2]
    if img_name.split(".")[-1] != 'pgm':
        # if not os.path.exists(img_name+'.'+img_ext):
        save_pgm(img, img_name)
    img.filename_pgm = basename+'.pgm'
    return img    
    
def save_pgm(img, img_name):
    '''
    this method converts the image to type P5 pgm image, with the same name, and saves it
    '''
    basename = img_name.split('.')[-2]
    img = Image.open(img_name).convert("L")
    img.save(basename+'.pgm')
    print 'Converting', img_name, 'to PGM complete!'