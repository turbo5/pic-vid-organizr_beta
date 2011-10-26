import sys,os
import getopt
# important for windows use!
import glob
#import argparse
import Image,ImageStat
from random import randint
import random
import EXIF
import settings
from k_means_plus_plus import *

from clustering import *
from image_module import resize_image, convert_to_pgm, ImageObject, prepare_img_for_sift,remove_temp_files_clusters, remove_temp_files_img, video_to_frames
from sift_turbo import get_descriptors, make_keypoints

USAGE_STRING = "usage: [-r REPEATS_NUM] [-c CLUSTERS_NUM] [-i] [-v] [-d] [-s] [PICTURE_FILES|--video VIDEO_FILE --fps FPS]\
[--mode scenes|joined] [--make_video]"
instr_video = '\nType the approx. num of scenes to start video separating (it may change): '
instr_clustering = '\nNote: num of clusters may change during SIFT / scene cut and join\n\
Press ENTER to start..(or type a num to custom num of clusters): '
    
try:
    argv=sys.argv[1:]
    optlist, args = getopt.getopt(argv, ':visr:dc:', ['video=','fps=','mode=','make_video'])
    optlist=dict(optlist)
    
    verbose='-v' in optlist
    interactive='-i' in optlist
    num_of_repeats=int(optlist.get('-r') or 1)
    num_of_clusters=optlist.get('-c') or None
    draw='-d' in optlist
    is_sift='-s' in optlist
    video=optlist.get('--video') or None
    fps=optlist.get('--fps') or None
    mode=optlist.get('--mode') or None
    make_video='--make_video' in optlist
except getopt.GetoptError:
    print USAGE_STRING
    exit(-1)
    
if len(args)==0:
    if video == None:
        print "Missing FILES parameter!"
        print USAGE_STRING
        exit(-1)
    else:
        if fps == None or mode == None:
            print 'In video mode, --video AND --fps AND --mode are required'
            print USAGE_STRING
            exit(-1)
        else:
            video_to_frames(video,fps)
            args = ['video_frames/*.jpg']
   
# important for windows use!
if settings.is_win and len(args)==1:
    args=glob.glob(args[0])

#~ parser = argparse.ArgumentParser(description='Image clustering program.')
#~ parser.add_argument('paths', metavar='FILES', type=file, nargs="+",
                   #~ help='the path to the images')
#~ parser.add_argument('--r', dest='num_of_repeat', metavar='REPEATS', default=1, type=int, help='Number of repeat clustering')
#~ parser.add_argument('--n', dest='num_of_clusters', metavar='CLUSTERS', type=int, help='Number of clusters')
#~ parser.add_argument('--i', dest='interactive', action='store_const',
                   #~ const=True, default=False, help='Interactive mode')
#~ parser.add_argument('--v', dest='verbose', action='store_const',
                   #~ const=True, default=False, help='verbose output')
#~ 
#~ args = parser.parse_args()
#~ num_of_clusters = args.num_of_clusters

if verbose:print "Extracting information from files..."
objects = []
for (counter,this_file) in enumerate(args):
    try:
        im = Image.open(this_file, 'r')
    except IOError:
        print 'File load error'
        
    else:
        stat = ImageStat.Stat(im)
        exif_data = EXIF.process_file(open(this_file, 'rb'))
        obj = ImageObject(this_file)
        
        for e in settings.EXIF_ATTRIBUTES:
            # Kvalitativ attributumok
            if len(e) == 1:
                try: obj.attributes[e[0]] = QualityAttr(exif_data[e[0]].printable, settings.WEIGHTS[e[0]])
                except: pass
            # kvantitativ attr-k, max ertekkel a normalashoz
            elif len(e) == 2:
                try: obj.attributes[e[0]] = QuantityAttr(clustering.eval_float(exif_data[e[0]].printable), settings.WEIGHTS[e[0]], e[1])
                except: pass
        
        #~ 
        #~ obj.attributes["EXIF DateTimeDigitized"] = DateAttr(exif_data["EXIF DateTimeDigitized"].printable, 1)
        #~         
        
        max_sum2 = (255**2)*im.size[0]*im.size[1]
        obj.attributes["sum2_R"] = QuantityAttr(stat.sum2[0], settings.WEIGHTS["sum2"], max_sum2)
        obj.attributes["sum2_G"] = QuantityAttr(stat.sum2[1], settings.WEIGHTS["sum2"], max_sum2)
        obj.attributes["sum2_B"] = QuantityAttr(stat.sum2[2], settings.WEIGHTS["sum2"], max_sum2)        
       
        obj.attributes["mean_R"] = QuantityAttr(stat.mean[0], settings.WEIGHTS["mean"], settings.max_mean)
        obj.attributes["mean_G"] = QuantityAttr(stat.mean[1], settings.WEIGHTS["mean"], settings.max_mean)
        obj.attributes["mean_B"] = QuantityAttr(stat.mean[2], settings.WEIGHTS["mean"], settings.max_mean)        
        
        obj.attributes["median_R"] = QuantityAttr(stat.median[0], settings.WEIGHTS["median"], settings.max_median)
        obj.attributes["median_G"] = QuantityAttr(stat.median[1], settings.WEIGHTS["median"], settings.max_median)
        obj.attributes["median_B"] = QuantityAttr(stat.median[2], settings.WEIGHTS["median"], settings.max_median)        
        
        obj.attributes["rms_R"] = QuantityAttr(stat.rms[0], settings.WEIGHTS["rms"], settings.max_rms)
        obj.attributes["rms_G"] = QuantityAttr(stat.rms[1], settings.WEIGHTS["rms"], settings.max_rms)
        obj.attributes["rms_B"] = QuantityAttr(stat.rms[2], settings.WEIGHTS["rms"], settings.max_rms)
                
        obj.attributes["var_R"] = QuantityAttr(stat.var[0], settings.WEIGHTS["var"], settings.max_var)
        obj.attributes["var_G"] = QuantityAttr(stat.var[1], settings.WEIGHTS["var"], settings.max_var)
        obj.attributes["var_B"] = QuantityAttr(stat.var[2], settings.WEIGHTS["var"], settings.max_var)
        
        objects.append(obj)
        
        if verbose: 
            print "%s (%s of %s)" % (this_file, counter+1, len(args))
            print 'num of attributes: ', len(obj.attributes), '\n'        

if verbose:print 'File processing complete.\n'
if len(objects)==0:
    print "Files not found! (Perhaps wrong parameter used)"
    print USAGE_STRING
    exit(-1)

best_clustering=None
while True:
    best_clustering_temp = None    
    if interactive:
        best_clustering_temp = best_clustering
        if video: user_input=raw_input('\n<type "x" to exit>'+instr_video)
        else: user_input=raw_input('\n<type "x" to exit>'+instr_clustering)
        if user_input=='x' or user_input=='X':
            if best_clustering_temp:
                remove_temp_files_clusters(best_clustering_temp.clusters, verbose)
            exit(0)
        # if video: num_of_clusters = 1
        else:
            try:        
                num_of_clusters = int(user_input)
            except:
                num_of_clusters = num_of_clusters

    if not num_of_clusters:
        if video: num_of_clusters = 1
        else:
            # default number...modified by plus 2
            num_of_clusters = int(math.sqrt(len(objects)/2)) + 2
    
    if len(objects)<int(num_of_clusters): num_of_clusters = len(objects)
    # objectek nullazas, elokeszites
    if verbose:print '\nPreparing images...\n'
    for img in objects:
        img.is_result = False
        img.was_matched_with = []
        # minden kepre: lemeretezes, pgm keszites, keypointok megtalalasa ha meg nem volt
        if is_sift:
            img = prepare_img_for_sift(img)
        
    if verbose:print 'Preparing images done\n' 

    best_clustering=None
    best_clustering_error=Decimal('Infinity')
    for i in range(num_of_repeats):
        if verbose:print '-----------------------------------'
        if verbose:print 'Repeat %s of %s' % (str(i+1),str(num_of_repeats))
        if verbose:print '-----------------------------------'
        #kmeans++
        initial_clusters=do_kmeans_plus_plus(objects,int(num_of_clusters))
        
        #random
        #initial_clusters=[[o] for o in random.sample(objects,num_of_clusters)]
        if video and fps:
            '''best_clustering = VideoSeparator(initial_clusters)
            best_clustering.make_initial_cluster(objects, verbose)'''
            clustering = VideoSeparator(initial_clusters)
        else:
            clustering = KMeans(initial_clusters)
        clustering.execute(objects, verbose)
        clustering.count_results_and_print_clustering(len(objects),verbose)
        error = clustering.total_squared_error()
        if verbose: clustering.print_error('clustering\'s total squared error:')
        
        if error < best_clustering_error:
            best_clustering = deepcopy(clustering)
            best_clustering_error = error            
    
    if is_sift:
        best_clustering.SIFT_matching(len(objects),verbose)
        best_clustering.count_results_and_print_clustering(len(objects),verbose)
        if not interactive: remove_temp_files_clusters(best_clustering.clusters, verbose)
    
    # check if clusters are separate scenes in the video
    if video and fps and mode:
        
        ######### implementalt metodusok
        # 1. egymast koveto (idoben) clustereket/sceneket probal meg joinolni (elso-utso kepek alapjan)
        # best_clustering.join_near_scenes_following(fps,program_mode=mode,check_mode=['AND'|'OR'|'time_diff'|'dist'|'length'|'sift'])
        
        # 2. barmely clustert/scenet barmellyel probal joinolni (kozepso-refpoint kepek alapjan)
        # #### DEPRECATED ####, inkabb a following hasznalata ajanlott; plane ha kmeans nelkul(v 1 klaszterrel) mukodik
        # best_clustering.join_near_scenes_any(fps,program_mode=mode,check_mode=['AND'|'OR'|'time_diff'|'dist'|'length'|'sift'])
        
        # clustereket szetvag scenekre (a 2 fuggveny igy egymas utan hasznalando; elso bejelol, masodik szetvag)
        # 'sift' modbna csak akkor vizsgalunk 2 kep kozott SIFT-et, ha CLUSTER_DISTANCE_TRESHOLD_MODE_SCENECUT_CHECK_SIFT feletti a tavjuk (optimalizalas)
        # 3.a. best_clustering.check_if_scenes(fps,program_mode=mode,check_mode=['AND'|'OR'|'time_diff'|'dist'|'sift'])
        # 3.b. best_clustering.cut_clusters_to_scenes()
        
        # ami scenek minden szetszedes es egyesites utan is kimaradtak es nagyon kicsik azokat torlom
        # best_clustering.delete_short_scenes(fps,program_mode=mode)       
        ######### VEGE implementalt metodusok 
        '''
        # ujraszamoljuk a ref pointokat a szetszedett scene klaszterekben
        best_clustering.count_results_and_print_clustering(len(objects),verbose=False)
        '''        
        
        best_clustering.check_if_scenes(fps,program_mode=mode,check_mode=['OR','dist'])
        best_clustering.cut_clusters_to_scenes()
        best_clustering.join_near_scenes_following(fps,program_mode=mode,check_mode=['OR','length', 'dist'])
                
        # best_clustering.delete_short_scenes(fps,program_mode=mode)
        
        best_clustering.check_repeated_scenes(fps,program_mode=mode,check_mode=['OR','dist'], make_video=make_video)
        
        # best_clustering.join_near_scenes_following(fps,program_mode=mode,check_mode=['AND','length','sift'])
        # best_clustering.join_near_scenes_following(fps,program_mode=mode,check_mode=['AND','length','dist'])        
        
        best_clustering.print_scene_starts(fps, mode, make_video)
    else:      
        ########### clustering END
        if verbose: best_clustering.print_error('best clustering\'s total sqared error:')
        best_clustering.print_chosens(verbose)
 
    if draw:
        if verbose:print '\nDrawing index image...'
        best_clustering.draw_clusters()
        if verbose:print 'Index image saved.'
    if not interactive:
        break

