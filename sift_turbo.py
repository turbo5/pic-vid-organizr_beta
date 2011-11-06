'''
sift wrapper by turbo
hibakezeles meg nem nagyon van :)
'''

from PIL import Image
from numpy import *
import numpy as np
import sift
import image_module as image_module
import os
import math

import settings
from image_module import *
        
def make_keypoints(img):
    '''
    makes, saves the key file
    '''
    if img.filename_resized: 
        name = img.filename_resized
    else: 
        name = img.filename
    kp_name = name.split('.')[-2] + '.key'
   
    if sift.process_image(img.filename_pgm, kp_name): 
        img.filename_keypoints = kp_name
        return img
    else: 
        print 'Error while making keypoints. Exit.'
        exit(-1)
    
def get_descriptors(img):
    # ImageObjectet var, aminek van mar filename_keypoints attributuma
    '''
    returns the image as array, the location of features, and the descriptors
    '''
    loc,desc = sift.read_features_from_file(img.filename_keypoints)
    return loc, desc

def get_qom(Ks, Kc, Km):
    #returns the quality of match between 2 images
    
    # if one of the pictures doesnt have kaypoints..no match
    if Ks==0 or Kc==0 or Km==0:
        return 0.0, 0
    
    Km = math.trunc(Km)
    Ks = math.trunc(Ks)
    Kc = math.trunc(Kc)
    R = Ks*1.0/Kc*1.0       
    
    if R<settings.KeypointsRatio_low: R=settings.KeypointsRatio_low
    if R>settings.KeypointsRatio_high: R=settings.KeypointsRatio_high    
    
    # alapesetben a MatchPercent a source kep keypointjai kozul a matchelok szazaleka
    # de lehet akar a compared kep keypointjai kozul a matcheloke is..
    # en itt azt veszem a ketto kozul, amelyik a nagyobb...jo kerdes.
    MatchPercent_source = Km*1.0/Ks*1.0 
    MatchPercent_compared = Km*1.0/Kc*1.0
    
    MatchPercent = None
    if (MatchPercent_source > MatchPercent_compared): MatchPercent = MatchPercent_source
    else: MatchPercent = MatchPercent_compared
    MatchPercent = MatchPercent*100.0
    
    # ha nagyon keves (settingsben allithato) a matching keypointok szama, azt buntetem qom-ben egy m parameterrel
    m = Km/settings.LOWEST_MATCHES_NUM*1.0
    if m>1.0: m=1.0
    else: m = math.pow(m,2)
    qom = MatchPercent*(1.0/R)*m
    
    return qom, MatchPercent

    
# get key point matches - from 2 pic
def get_kpm(img1,img2, mode='string' ,less=0, from_index=-1, to_index=-1):
    # in string mode, img1, img2 parameters are only strings (path to image files) -> testing, presentation, prints out infos
    # in only_match mode, these are ImageObject objects, no prints. 2 params are 2 [loc,desc] lists
    
    if mode=='string':
        print 'Preparing images...'  
        
    im1 = None
    im2 = None
    loc1, desc1 = None, None
    loc2, desc2 = None, None
    # only_match mod eseten a gyorsabb futas miatt csak a match-et nezem, a tobbi erteket elore kiszamolom a kepekre
    if mode=='string':
        img1 = image_module.convert_to_pgm(img1)
        img2 = image_module.convert_to_pgm(img2)
        img1 = make_keypoints(img1)
        img2 = make_keypoints(img2)
        
        loc1, desc1 = get_descriptors(img1)
        loc2, desc2 = get_descriptors(img2)
        
        im1 = get_image_as_array(img1)
        im2 = get_image_as_array(img2)
    elif mode=='only_match':
        loc1 = img1[0]
        desc1 = img1[1]
        loc2 = img2[0] 
        desc2 = img2[1]
    else:
        print 'Not supported mode!'
        exit(-1)
    
    if mode=='string': print '\nSearching for matchings...'
    matchscores = sift.match(desc1, desc2)
    
    bool_indexing = False    
    
    # ezzel a 2 indexxel kivalasztom mettol meddig levo matched keypointokat akarom kirajzolni..atlathatosag
    if from_index>to_index:
        from_index = -1
        to_index = -1
    if from_index!=-1 and to_index!=-1:
        bool_indexing = True
    if bool_indexing:
        if from_index<1: from_index = 1
        if to_index>matchscores.size: to_index = matchscores.size
    
    # because of the 4x4 storing method in lowe's paper
    num_keypoints1 = loc1.size/4
    num_keypoints2 = loc2.size/4
    
    num_matches = nonzero(matchscores)[0].size
    if mode=='string':        
        for counter, m in enumerate(matchscores.tolist()):
            if bool_indexing and (not from_index-1<=counter<=to_index-1):
                matchscores[counter] = np.float64(0.0)
            else:
                # ezzel a parameterrel minden 'less'-edik matchet rajzolja csak ki..atlathatosag miatt ugyancsak                
                if less != 0:
                    if counter % less != 0: matchscores[counter] = np.float64(0.0)
    
    print "Number of matching keypoints:", num_matches
    if mode=='string':
        print "number of displayed matches:", nonzero(matchscores)[0].size
    
    qom, MatchPercent = get_qom(num_keypoints1, num_keypoints2, num_matches)
    print "Quality of match: ", qom, '\n'
    
    return im1, im2, matchscores,qom,MatchPercent

def get_image_as_array(img):
    # ImageObject -et var aminek van mar pgm file-ja (filename_pgm attributum)
    im = array(Image.open(img.filename_pgm))
    return im      
    
def get_kpm_string(img1,img2,mode='string',less=0, from_index=-1, to_index=-1):
    img1 = ImageObject(img1)
    img2 = ImageObject(img2)
    
    i1,i2,m,q,mp = get_kpm(img1,img2, mode,less, from_index, to_index)
    image_module.remove_temp_files_img(img1)
    image_module.remove_temp_files_img(img2)
    
    return i1,i2,m,q,mp
    
    
def plot_kp(img, mode='string'):
    img = ImageObject(img)
    img = image_module.convert_to_pgm(img)
    img = make_keypoints(img)
    
    loc, desc = get_descriptors(img)
    im = get_image_as_array(img)
    sift.plot_features(im,loc)
    image_module.remove_temp_files_img(img)
    
def plot_kpm(img1,img2,mode='string',less=0, from_index=-1, to_index=-1):
    if mode == 'string':
        img1 = ImageObject(img1)
        img2 = ImageObject(img2)
    im1, im2, matchscores,qom,MatchPercent = get_kpm(img1,img2, mode,less, from_index, to_index)
    
    loc1, desc1 = get_descriptors(img1)
    loc2, desc2 = get_descriptors(img2)
    
    sift.plot_matches(im1,im2,loc1,loc2,matchscores)
    image_module.remove_temp_files_img(img1)
    image_module.remove_temp_files_img(img2)
    