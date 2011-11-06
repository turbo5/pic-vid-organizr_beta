import Image
import ImageDraw
import math
from decimal import *
from datetime import datetime
from datetime import timedelta
from copy import deepcopy
from time import *
from operator import itemgetter, attrgetter
import re
import os
import settings

from image_module import prepare_img_for_sift, remove_temp_files_img, draw_text_on_img, frames_to_video, remove_file_img
from sift_turbo import get_kpm

'''
yuml.me
[Object|+attributes|+get_distance(vector){bg:green}]^[ImageObject|+filename;+path{bg:green}]
[ClusteringAlgorithm|-clusters|-get_get_ref_point(cluster);+execute(objects){bg:orange}]^[KMeans||-iterate(objects){bg:orange}]
[ClusteringAlgorithm]<>1-0..*>[Object]

'''
def are_scenes_joinable(diff,fps,dist,program_mode,check_mode,img1=None,img2=None, length_diff=None,similar_check=False):
    # h nem-e lognak egymasba
    if diff > 0:        
        DIST_TRESH = None
        TIMEDIFF_TRESH = None
        DISTANCE_TRESH_CHECK_SIFT = None
        if program_mode == 'scenes': 
            DIST_TRESH = settings.CLUSTER_DISTANCE_TRESHOLD_MODE_SCENECUT
            if similar_check:
                DIST_TRESH = settings.CLUSTER_DISTANCE_TRESHOLD_SIMILAR_CHECK
            TIMEDIFF_TRESH = settings.TIMEDIFF_TRESH_MODE_SCENECUT
            LENGTH_TRESH = settings.LENGTH_TRESH_MODE_SCENECUT
            DISTANCE_TRESH_CHECK_SIFT = settings.CLUSTER_DISTANCE_TRESHOLD_MODE_SCENECUT_CHECK_SIFT
        elif program_mode == 'joined': 
            DIST_TRESH = settings.CLUSTER_DISTANCE_TRESHOLD_MODE_JOINCUT
            if similar_check:
                DIST_TRESH = settings.CLUSTER_DISTANCE_TRESHOLD_SIMILAR_CHECK
            TIMEDIFF_TRESH = settings.TIMEDIFF_TRESH_MODE_JOINCUT
            LENGTH_TRESH = settings.LENGTH_TRESH_MODE_JOINCUT
            DISTANCE_TRESH_CHECK_SIFT = settings.CLUSTER_DISTANCE_TRESHOLD_MODE_JOINCUT_CHECK_SIFT
        
        results = []
        
        was_joined_by_dist = False
        if 'dist' in check_mode:
            if dist < DIST_TRESH:
                results.append(True)
                was_joined_by_dist = True
            else:
                results.append(False)
        
        if 'sift' in check_mode and img1 and img2:
            if not was_joined_by_dist:
                dist = img1.get_distance(img2,from_object=True)
                if dist > DISTANCE_TRESH_CHECK_SIFT:
                    img1 = prepare_img_for_sift(img1)
                    img2 = prepare_img_for_sift(img2)
                    loc_desc1 = (img1.loc, img1.desc)
                    loc_desc2 = (img2.loc, img2.desc)
                    im1, im2, mscores,qom,mpercent = get_kpm(loc_desc1, loc_desc2, mode='only_match')
                    if qom > settings.QOM_MINIMUM_SCENEJOIN:
                        results.append(True)
                    else:
                        results.append(False)        
        
        if 'length' in check_mode:
            length_time = frame_diff_to_milisecs(length_diff,fps)
            if length_time <= float(LENGTH_TRESH)*1000.0:
                results.append(True)
            else:
                results.append(False)
            
        if 'time_diff' in check_mode:
            time_diff = frame_diff_to_milisecs(diff,fps)
            if time_diff<(float(TIMEDIFF_TRESH)*1000.0):
                results.append(True)
            else:
                results.append(False)
    
        if 'AND' in check_mode:
            if False in results: return False
            else: return True
        if 'OR' in check_mode:
            if True in results: return True
            else: return False
        
    else:
        return False
    
def is_scene_separable(diff,fps,program_mode,check_mode,img1,img2):
    if diff>1: return True
    DIST_TRESH = None
    TIMEDIFF_TRESH = None
    DISTANCE_TRESH_CHECK_SIFT = None
    if program_mode == 'scenes': 
        DIST_TRESH = settings.CLUSTER_DISTANCE_TRESHOLD_MODE_SCENECUT
        TIMEDIFF_TRESH = settings.TIMEDIFF_TRESH_MODE_SCENECUT
        DISTANCE_TRESH_CHECK_SIFT = settings.CLUSTER_DISTANCE_TRESHOLD_MODE_SCENECUT_CHECK_SIFT
    elif program_mode == 'joined': 
        DIST_TRESH = settings.CLUSTER_DISTANCE_TRESHOLD_MODE_JOINCUT
        TIMEDIFF_TRESH = settings.TIMEDIFF_TRESH_MODE_JOINCUT
        DISTANCE_TRESH_CHECK_SIFT = settings.CLUSTER_DISTANCE_TRESHOLD_MODE_JOINCUT_CHECK_SIFT
        
    results = []
        
    if 'time_diff' in check_mode:
        time_diff = frame_diff_to_milisecs(diff,fps)
        if time_diff>(float(TIMEDIFF_TRESH)*1000.0):
            results.append(True)
        else:
            results.append(False)
    
    was_separated_by_dist = False
    if 'dist' in check_mode:
        dist = img1.get_distance(img2,from_object=True)
        # print 'img1',img1.get_only_num(),'img2',img2.get_only_num(),'dist',dist,'DIST_TRESH',DIST_TRESH
        if dist > DIST_TRESH:
            was_separated_by_dist = True
            results.append(True)
        else:
            results.append(False)

    if 'sift' in check_mode and img1 and img2:
        if not was_separated_by_dist:
            dist = img1.get_distance(img2,from_object=True)
            if dist > DISTANCE_TRESH_CHECK_SIFT:
                img1 = prepare_img_for_sift(img1)
                img2 = prepare_img_for_sift(img2)
                loc_desc1 = (img1.loc, img1.desc)
                loc_desc2 = (img2.loc, img2.desc)
                im1, im2, mscores,qom,mpercent = get_kpm(loc_desc1, loc_desc2, mode='only_match')
                # print 'img1',img1.get_only_num(),'img2',img2.get_only_num(),'qom',qom,'QOM_MINIMUM_SCENECUT',settings.QOM_MINIMUM_SCENECUT
                if qom < settings.QOM_MINIMUM_SCENECUT:
                    results.append(True)
                else:
                    results.append(False)            
                
    if 'AND' in check_mode:
        if False in results: return False
        else: return True
    if 'OR' in check_mode:
        if True in results: return True
        else: return False
            
def eval_float(e):
    if '/' in e:
        return float(e.split('/')[0])/float(e.split('/')[1])
    else:
        return int(e)

def frame_diff_to_milisecs(frame_diff,fps):        
    return int(frame_diff)*(1.0/eval_float(fps))*1000.0

def GetInHMS(miliseconds):
    seconds = miliseconds / 1000
    # miliseconds = int(math.floor(miliseconds/1000.0))
    hours = seconds / 3600
    seconds -= 3600*hours
    minutes = seconds / 60
    seconds -= 60*minutes
    # if hours == 0:
        # return "%02d:%02d" % (minutes, seconds)
    return "%02d:%02d:%02d" % (hours, minutes, seconds)
    
def avg_time(a):
    epoch = datetime.fromtimestamp(mktime(gmtime(0)))

    numdeltas = len(a)
    sumdeltas = timedelta(seconds=0)
    
    for i in a:
        delta = abs(i-epoch)
        try:
            sumdeltas += delta
        except:
            raise
    avg = sumdeltas / numdeltas
    return epoch+avg
    
class Attribute():
    value = None
    weight = None
    
    def __init__(self,value,weight):
        self.value = value
        self.weight = weight
    
    def divide(self,n):
        raise NotImplementedError( "Should have implemented this" )

    def compare(self,Attribute):
        raise NotImplementedError( "Should have implemented this" )

class QuantityAttr(Attribute):
    max_value = None
    
    def __init__(self,value,weight, max_value):
        Attribute.__init__(self,value,weight)
        self.max_value = max_value
        self.value = min(float(value)/max_value, 1)
    
    def add(self,other):
        self.value+=other.value
        
    def divide(self,n):
        self.value/=n
        
    def compare(self,other):
        return self.value-other.value

class QualityAttr(Attribute):
    
    def __init__(self,value,weight):
        Attribute.__init__(self,value,weight)
        self.value = {value:1}
        
    def add(self,other):
        for k,v in other.value.items():
            if k in self.value:
                self.value[k]+=v
            else:
                self.value[k]=v
    
    def divide(self,n):
        pass
    
    def compare(self,other):
        d=deepcopy(other.value)
        m=max(v for k,v in other.value.items())
        for k,v in d.items():
            d[k]=abs(float(v-m))/m
            
        #print d
        #print self.value.items()
        my_key = self.value.items()[0][0]
        if my_key in d:
            #print d[my_key]
            return d[my_key]
        else:
            #print 1
            return 1

        #return [1,0][self.value==other.value]

class DateAttr(Attribute):
    format = None
    
    datetimes = []
    
    def __init__(self,value,weight,format='%Y:%m:%d %H:%M:%S'):
        Attribute.__init__(self,value,weight)
        self.format = format
        self.datetimes=[datetime.strptime(self.value,self.format)]
    
    def add(self, other):
        self.datetimes.append(datetime.strptime(other.value,other.format))
        
    def divide(self,n):
        #self.datetimes.sort()
        self.value = avg_time(self.datetimes).strftime('%Y:%m:%d %H:%M:%S')
        
        #self.value = (min(self.datetimes) + (max(self.datetimes)-min(self.datetimes))/2 ).strftime('%Y:%m:%d %H:%M:%S')
        self.datetimes=[datetime.strptime(self.value,self.format)]
    
    def compare(self,other):
        d1 = datetime.strptime(self.value,self.format)
        d2 = datetime.strptime(other.value,other.format)
        d = abs(d2-d1)
        diff = d.days + d.seconds
        #normalt ertke a kolonbsegnek mp alapjan, a globalis DATE_MAX ertek szerint levagva
        return min(float(diff)/settings.DATE_MAX, 1)


class ClusteringAlgorithm():
    clusters=[]
    
    def __init__(self, clusters):
        self.clusters= clusters
        
    def get_ref_point(self,cluster):
        pass
    
    def execute(self, objects, verbose):
        pass
        
    def count_results_and_print_clustering(self,objects_num, verbose):
        pass        
    
    def draw_clusters(self,results=None):
        WIDTH = 1000
        HEIGHT = 30
        for cluster in self.clusters:
            HEIGHT+=(int((len(cluster)*110)/WIDTH)+1)*110 + 70
        
        out = Image.new('RGBA', (WIDTH,HEIGHT))
        draw = ImageDraw.Draw(out)
        x=10
        y=10
        n=0
        # for n, cluster in zip(range(len(self.clusters)), self.clusters):
        for cluster in sorted(self.clusters,key= lambda cl: cl[0].get_only_num()):
            draw.rectangle((0, y-2, WIDTH, y+12), fill=(0,0,250))
            draw.text((x,y),'Cluster #%s (%s objects)' % (n+1,len(cluster)))
            y+=20
            for img in self.get_cluster_sorted(n):
                if x>=WIDTH-110:
                    x = 10
                    y+= 140
                im = Image.open(img.filename)
                im.thumbnail((100,100), Image.ANTIALIAS)
                if img.is_result:
                    draw.rectangle(((x-5,y-5),(x+105,y+135)),255)
                out.paste(im, (x,y+12))
                
                draw.text((x,y),img.get_only_filename())
                if img.flag_move_to_clusternum:
                    draw.text((x,y+im.size[1]+31),'#'+str(img.flag_move_from_clusternum+1)+' -> #'+str(img.flag_move_to_clusternum+1))
                if img.sceneNum:
                    draw.text((x,y+im.size[1]+41),'scene num: '+str(img.sceneNum))
                if img.matched:
                    # draw.rectangle((x, y+12, x+im.size[0], y+12+18), fill=(255,255,255))
                    draw.text((x,y+im.size[1]+11),img.matched.get_only_filename())
                    draw.text((x,y+im.size[1]+21),str(img.matching_qom))
                x+=100+10
            x=10
            y+=140
            n+=1
                
        #out.show()
        out.save("_output.jpg", "JPEG")


    def total_squared_error(self):
        e=0
        for cluster in self.clusters:
            rf = self.get_ref_point(cluster)
            for o in cluster:
                e+=o.get_distance(rf)**2
        return e
        
class KMeans(ClusteringAlgorithm):
    
    def make_initial_cluster(self):
        pass

    def get_distance_between_two_img(self,o1,o2):
        # distance = sqrt(((P1-Q1)^2 + (P1-Q1)^2 + ... + (Pn-Qn)^2)/n)
        s=0
        n=0
        for (k,a1) in o1.attributes.items():
            if o2.attributes.get(k):
                n+=1
                a2 = o2.attributes.get(k)
                d=(a1.compare(a2))**2
                d*=a1.weight
                s+=d
        if n==0: return Decimal('Infinity')
        else: return math.sqrt(s/n)
        
    def get_ref_point(self,cluster):
        
        ref_point={}
        for o in cluster:
            for k,v in o.attributes.items():
                if k in ref_point:
                    ref_point[k].add(v)
                else:
                    ref_point[k]=deepcopy(v)
        
        for k,v in ref_point.items():
            ref_point[k].divide(len(cluster))
        
        return ref_point

    def iterate(self,objects):
        changes = 0
        for o in objects:
            min_distance=Decimal('Infinity')
            closest_cluster=None
            
            for c in self.clusters:
                rf = self.get_ref_point(c)
                if o.get_distance(rf)<min_distance:
                    min_distance = o.get_distance(rf)
                    closest_cluster=c
            
            try:
                closest_cluster.index(o)
            except ValueError:
                #kivesz mindenhonnan
                for cl in self.clusters:
                    try:
                        cl.remove(o)
                        #print '%s-t kivesz #%s-bol' % (o.filename,self.clusters.index(cl))
                    except ValueError:
                        pass
                #beletesz ide
                closest_cluster.append(o)
                #print '%s-t betesz #%s-be' % (o.filename,self.clusters.index(closest_cluster))
                changes+=1
                
        return changes
        
    def execute(self, objects, verbose):
        for i in range(6):
            if verbose: print "iteration", i
            ch = self.iterate(objects)
            if verbose: print ch, "changes"
            if ch==0: break
            if verbose: print [len(c) for c in self.clusters]
        
        #~ top_cluster = max([(len(c),c) for c in self.clusters])[1]
        #~ ref_point = self.get_ref_point(top_cluster)
        #~ closest_to_ref_point = min([(o.get_distance(ref_point),o) for o in top_cluster])[1]
        #~ return closest_to_ref_point        
    
     
    def get_cluster_sorted(self,clusterNum):
        return sorted(self.clusters[clusterNum], key=attrgetter('filename'))
    
    def del_empty_clusters(self):
        flags_delete = []
        for counter, cluster in enumerate(self.clusters):
            if len(cluster) < 1: flags_delete.append(counter)
        for del_num in reversed(flags_delete):
            del self.clusters[del_num]
    
    def get_closest_to_ref_point(self,cluster):
        ref_point = self.get_ref_point(cluster)
        # print len(cluster)
        return min([(o.get_distance(ref_point),o) for o in cluster])[1]
    
    def count_results_and_print_clustering(self,objects_num, verbose):
        # tisztogatas, nullazasok, ha tobbszor hivjuk
                
        '''
        # ures clustereket torlom a clusterek kozul
        flags_delete = []
        for counter, cluster in enumerate(self.clusters):
            if len(cluster) < 1: flags_delete.append(counter)
        for del_num in reversed(flags_delete):
            del self.clusters[del_num]
        '''
        # is_result, azaz kivalasztott kep tul is torlom, ujraklaszterezes esetere
        for cluster in self.clusters:
            for i in cluster:
                i.is_result = False        
        
        min_size = int(math.ceil(objects_num*settings.MIN_SIZE_OF_RELEVANT_CLUSTER))
        if verbose: print 'Min cluster size for thumbnail: ' + str(min_size)
        for counter,c in enumerate(self.clusters):
            if len(c)>0 and len(c)>=min_size:                
                closest_to_ref_point_img = self.get_closest_to_ref_point(c)
                closest_to_ref_point_img.is_result = True
                
                if verbose: print 'Cluster #%s size: %s ---> %s' % (str(counter+1), str(len(c)), closest_to_ref_point_img.get_only_filename())
            else:
                if verbose: print 'Cluster #%s size: %s' % (str(counter+1), str(len(c)))
        
    def print_error(self,string):
        print '-----------------------------------'
        print string+' '+str(self.total_squared_error())
        print '-----------------------------------\n'        
        
    def print_chosens(self, verbose):
        results = []
        for c in self.clusters:
            for i in c:
                if i.is_result: results.append(i)        
        
        # kivettem nem tom mi.. ha nincs eredmeny egy sem? miert?
        # if len(results)==0:
            # max_cluster = max([(len(c),c,counter) for (counter,c) in enumerate(self.clusters)])
            # top_cluster = max_cluster[1]
            # ref_point = self.get_ref_point(top_cluster)
            # closest_to_ref_point = min([(o.get_distance(ref_point),o) for o in top_cluster])[1]            
            # closest_to_ref_point.is_result = True
            # results = [closest_to_ref_point]
            # if verbose: print 'Cluster #%s size: %s ---> %s' % (max_cluster[2]+1, str(len(top_cluster)), closest_to_ref_point.get_only_filename())        
        
        if verbose:print 'Chosen pictures:'
        if verbose:
            for r in results:
                print r.get_only_filename()

    def SIFT_matching(self,objects_num,verbose):
        ########### SIFT 
        # minden kepet osszehasonlitok a settingsben beallitott mennyiseguvel/modon..
        if verbose:print '\nSIFT reclustering..'
                
        
        total_attempts = objects_num
        # objektum egyezesek keresese
        if verbose:print '\nSearching for SIFT matchings...'
        LS = settings.LESS_MATCHES_ATTEMPT_SOURCE
        LC = settings.LESS_MATCHES_ATTEMPT_COMPARED
        S=1
        C=1
        if LS>1: S = int(math.ceil(1.0*total_attempts/(1.0*LS)))
        else: S = total_attempts
        if LC>1: C = int(math.ceil(1.0*(total_attempts)/(1.0*LC)))
        else: C = total_attempts
        if LS<2: LS = 0        
        if LC<2: LC = 0
        
        total_attempts = (S*(C-1))/2
        co = 0
        
        # egyelore mindet mindennel (kiveve magaval)
        # lehetne maskepp, pl mindet csak ref pointokkal
        matches_num = 0
        for counter_source_cluster, cluster in enumerate(self.clusters):            
            for counter_source, source in enumerate(cluster):                
                if (LS==0 or (LS!=0 and counter_source % LS == 0)):
                    for counter_compared_cluster, cluster2 in enumerate(self.clusters):            
                        for counter_compared, compared in enumerate(cluster2):
                            if source.get_only_filename() != compared.get_only_filename():
                                if (LC==0 or (LC!=0 and counter_compared % LC == 0)):
                                    # ha meg ez a source file nem volt osszehasonlitva a compareddel
                                    # k*(k-1)/2 osszehasonlitas, teljes graf. odavissza nem hasonlitok...kicsi ertelme lehetne SIFT miatt talan,
                                    # de igy fele annyi futasi ido
                                    if not source.get_only_filename() in compared.was_matched_with:
                                        co += 1
                                        print '\n(', co, 'of approx.', total_attempts, ') matching attempt'
                                        loc_desc1 = (source.loc, source.desc)
                                        loc_desc2 = (compared.loc, compared.desc)
                                        im1, im2, mscores,qom,mpercent = get_kpm(loc_desc1, loc_desc2, mode='only_match')
                                        if qom > settings.QOM_minimum:
                                            if verbose: print 'matched images:', source.get_only_filename(), '<->', compared.get_only_filename()
                                            matches_num += 1
                                            if source.matching_qom:
                                                if source.matching_qom < qom:
                                                    if verbose: print 'Better QOM image match found'
                                                    source.matched = compared
                                                    source.matching_qom = qom                                                    
                                            else:
                                                source.matched = compared
                                                source.matching_qom = qom                                
                                        if source.matched and (source.matched.get_only_filename() == compared.get_only_filename()):
                                            if source.matching_qom <= qom:    
                                                if not source.matched in cluster:
                                                    # mikor rakjuk at masik clusterbe?:
                                                    '''
                                                    dist_fromClusterRefpoint = source.get_distance(self.get_ref_point(cluster))
                                                    dist_toClusterRefpoint = source.get_distance(self.get_ref_point(cluster2))
                                                    '''
                                                    # print cluster[0].get_only_filename(),dist_fromClusterRefpoint,cluster2[0].get_only_filename(),dist_toClusterRefpoint
                                                    '''if dist_fromClusterRefpoint > dist_toClusterRefpoint:'''
                                                    if verbose: print "* Image flagged to move"                                                    
                                                    source.flag_move_from_clusternum = counter_source_cluster
                                                    source.flag_move_to_clusternum = counter_compared_cluster
                                    source.was_matched_with.append(compared.get_only_filename())                                  
                                    
        # reclustering
        # moving flagged objects to the right cluster
        moved = 0
        for counter_cluster, cluster in enumerate(self.clusters):
            for counter_image, image in enumerate(cluster):
                if image.flag_move_to_clusternum and (image.flag_move_to_clusternum != counter_cluster):
                    moved += 1
                    # TODO: melyiket rakjam melyikbe? mi alapjan? cluster meretek? tav a centroidtol?
                    # ha 1 marad csak a clusterben, azt is inkabb elrakjam?
                    # 1 meret clusterek a legnagyobb QOMeshez at?
                    img_to_move = cluster.pop(counter_image)                
                    self.clusters[image.flag_move_to_clusternum].append(img_to_move)
        if verbose: print '\n\nMoving', moved, 'images to other clusters done'
                            
        if verbose:print 'Found SIFT matchings SUM:', matches_num
        if verbose:print '\nSearching for SIFT matchings done'        
        
        if verbose:print 'SIFT reclustering ended\n'
        ############# END SIFT
        
        
class VideoSeparator(KMeans):

    def make_initial_cluster(self,objects,verbose):
        for o in objects:
            self.clusters[0].append(o)

    def print_scene_starts(self,fps, mode, make_video):
        if mode=='scenes': 
            print '\n\n####### Scenes (time: hh:mm:ss) #######'
            text = 'Scene: # %d'
        elif mode=='joined':
            print '\n\n####### Videos (time: hh:mm:ss) #######'
            text = 'Video: # %d'
        i = 0
        for cluster in sorted(self.clusters,key= lambda cl: cl[0].get_only_num()):
            i+=1
            clIndex = self.clusters.index(cluster) 
            scene_firstImg = self.get_cluster_sorted(clIndex)[0]
            frame_timeDiff_msec = (1.0/eval_float(fps))*1000.0
            scene_startTime = (scene_firstImg.get_only_num()*frame_timeDiff_msec)-frame_timeDiff_msec
            # kis igazitas, scenek kezdesi idejet korabbra veszem egy frame_timediff-nyi idovel,
            # hogy kezdes elotti legyen inkabb...mint utana
            scene_startTime -= frame_timeDiff_msec
            if scene_startTime < 0.0: scene_startTime = 0.0
            print '#',i,'start time:',GetInHMS(int(scene_startTime)),'; start img:',scene_firstImg.get_only_filename()
                            
            if make_video:
                for img in cluster:
                    draw_text_on_img(img.filename, text % (i))
        print '\n'
        
        if make_video:
            frames_to_video('_output.avi', fps)
    
    def check_repeated_scenes(self,fps,program_mode,check_mode, make_video):
        similars = []
        for cluster1 in sorted(self.clusters,key= lambda cl: cl[0].get_only_num())[:len(self.clusters)-1]:
            clCounter1 = sorted(self.clusters,key= lambda cl: cl[0].get_only_num()).index(cluster1)
            for cluster2 in sorted(self.clusters,key= lambda cl: cl[0].get_only_num())[(clCounter1+1):]:                
                clCounter2 = sorted(self.clusters,key= lambda cl: cl[0].get_only_num()).index(cluster2)
                img1 = self.get_closest_to_ref_point(cluster1)
                img2 = self.get_closest_to_ref_point(cluster2)
                dist = self.get_distance_between_two_img(img1,img2)
                diff = int(math.fabs(img1.get_only_num()-img2.get_only_num()))
                # print '----> ', img1.get_only_num(), img2.get_only_num(), 'dist', dist, 'diff', diff
                if are_scenes_joinable(diff,fps,dist,program_mode,check_mode,img1,img2, None,True):
                    similars.append((clCounter1,clCounter2))
        
        for s in sorted(similars, key= lambda s: s[0], reverse=False):
            print 'SIMILAR SCENES: #',s[0]+1, ' - #', s[1]+1
        
        if make_video:
            cluster_similars = {}
            for s in sorted(similars, key= lambda s: s[0], reverse=False):
                cluster_similars[s[0]] = []
            for s in sorted(similars, key= lambda s: s[1], reverse=False):
                cluster_similars[s[1]] = []
            
            for s in sorted(similars, key= lambda s: s[0], reverse=False):
                cluster_similars[s[0]].extend([s[1]+1])
            for s in sorted(similars, key= lambda s: s[1], reverse=False):
                cluster_similars[s[1]].extend([s[0]+1])
            
            for k, v in cluster_similars.iteritems():
                print v
                for img in sorted(self.clusters,key= lambda cl: cl[0].get_only_num())[k]:    
                    draw_text_on_img(img.filename, 'Similars: %s' % v, right=True, mult=len(v))
            
            '''
            clCounter = 0
            for cluster in self.clusters:
                cluster_similars = []
                for s in sorted(similars, key= lambda s: s[0], reverse=False):
                    if clCounter in ss:
                        c2_index = ss[(ss.index(clCounter)+1)%2]
                        cluster_similars.append(c2_index+1)
                if cluster_similars:
                    for img in self.clusters[clCounter]:                                        
                        draw_text_on_img(img.filename, 'Similars: %s' % cluster_similars, right=True, mult=len(cluster_similars))
                    cluster_similars = []
                clCounter += 1
            '''
    def check_if_scenes(self,fps,program_mode,check_mode):        
        clCounter = 0
        for cluster in sorted(self.clusters,key= lambda cluster: cluster[0].get_only_num()):
            self.separate_scenes(fps,clCounter,program_mode,check_mode)
            clCounter+=1    
    
    def separate_scenes(self,fps,clCounter,program_mode,check_mode):        
        counter_imgFrom = 0                
        
        clusterLength = None        
        is_last_pic = False
        for counter_imgTo, imgTo in enumerate(self.get_cluster_sorted(clCounter)[1:]):
            clusterLength = len(self.get_cluster_sorted(clCounter))
            if clusterLength > 1:
                imgCompare = self.get_cluster_sorted(clCounter)[counter_imgTo]
                imgCompare_orderNum = imgCompare.get_only_num()
                counter_imgTo += 1
                imgTo_orderNum = imgTo.get_only_num()
                
                # ha tobb a tav 2 kep kozott mint a hatar, vagunk
                
                diff = imgTo_orderNum - imgCompare_orderNum
                if clusterLength==counter_imgTo+1: is_last_pic = True
                if is_last_pic or is_scene_separable(diff,fps,program_mode,check_mode,imgTo,imgCompare) == True:
                    # megjeloljuk h ezek a kepek egy jelenetet alkotnak
                    sceneTo = counter_imgTo
                    if is_last_pic:
                        sceneTo +=1
                        if is_scene_separable(diff,fps,program_mode,check_mode,imgTo,imgCompare) == False:
                            self.get_cluster_sorted(clCounter)[-2].sceneNum = self.get_cluster_sorted(clCounter)[-2].get_only_num()
                            self.get_cluster_sorted(clCounter)[-1].sceneNum = self.get_cluster_sorted(clCounter)[-1].get_only_num()
                    else:
                        for img in self.get_cluster_sorted(clCounter)[counter_imgFrom:sceneTo]:
                            img.sceneNum = self.get_cluster_sorted(clCounter)[counter_imgFrom].get_only_num()
                    counter_imgFrom = counter_imgTo
                    
        # if clusterLength > 1:
            # imgLast = self.get_cluster_sorted(clCounter)[-1]
            # imgBeforeLast = self.get_cluster_sorted(clCounter)[-2]
            # imgLast_orderNum = int(imgLast.get_only_num())
            # imgBeforeLast_orderNum = int(imgBeforeLast.get_only_num())
            
            # diff = imgLast_orderNum - imgBeforeLast_orderNum
            
            # if is_scene_separable(diff,fps,program_mode,check_mode,imgLast,imgBeforeLast) == True:
                # self.get_cluster_sorted(clCounter)[-1].sceneNum = counter_img_temp
    
    def cut_clusters_to_scenes(self):
        # cutting scenes / removing images from clusters
        imgsToMove = {}
        for clCounter, cluster in enumerate(self.clusters):     
            imgsToMove[clCounter] = []
            for counter_img, img in enumerate(self.get_cluster_sorted(clCounter)):
                if img.sceneNum:                                           
                    popPlace = cluster.index(img)           
                    imgToMove = cluster.pop(popPlace)                                        
                    imgsToMove[clCounter].extend([imgToMove])
                    
        # making the new scene clusters
        for clusterCounter,cluster in imgsToMove.iteritems():
            if len(cluster)>0:                
                sceneNum_temp = cluster[0].sceneNum
                new_cluster = [cluster[0]]
                imgCounter = 0
                for img in cluster[1:]:
                    imgCounter+=1
                    if img.sceneNum != sceneNum_temp:
                        self.clusters.append(new_cluster)
                        new_cluster = []
                    if imgCounter+1==len(cluster):
                        new_cluster.append(img)
                        self.clusters.append(new_cluster)
                    new_cluster.append(img)
                    sceneNum_temp = img.sceneNum
                    
        self.del_empty_clusters()
     
    def delete_short_scenes(self,fps,program_mode):
        # tul rovid sceneket(clusterek) torlom a clusterek kozul
        MIN_SCENE_LENGTH = None
        if program_mode == 'scenes':             
            MIN_SCENE_LENGTH = settings.MIN_SCENE_LENGTH_MODE_SCENECUT
        elif program_mode == 'joined':             
            MIN_SCENE_LENGTH = settings.MIN_SCENE_LENGTH_MODE_JOINCUT
            
        flags_delete = []        
        for clCounter, cluster in enumerate(self.clusters):
            if len(cluster)>0:
                orderNum1 = cluster[0].get_only_num()
                orderNum2 = cluster[-1].get_only_num()
                time_diff_msec = int(orderNum2 - orderNum1)*(1.0/eval_float(fps))*1000.0
                # print MIN_SCENE_LENGTH*1000.0
                if MIN_SCENE_LENGTH*1000.0 >= time_diff_msec: flags_delete.append(clCounter)
        for del_num in reversed(flags_delete):
            for img in self.clusters[del_num]:
                remove_temp_files_img(img)
                # remove_file_img(img)
            del self.clusters[del_num]
    
    # az idoben egymast koveto sceneket probalom, min cluster distance (settings) eseten koztuk join
    def join_near_scenes_following(self,fps,program_mode,check_mode):
        clIndex_temp = None
        to_cluster_nums = []
        for cluster in sorted(self.clusters,key= lambda cluster: cluster[0].get_only_num()):
            clIndex = self.clusters.index(cluster)
            if clIndex_temp or clIndex_temp==0:
                img1 = self.clusters[clIndex][0]
                img2 = self.clusters[clIndex_temp][-1]
                diff = img1.get_only_num()-img2.get_only_num()
                dist = img1.get_distance(img2,from_object=True)
                # self.clusters[clIndex_temp]
                second_len_diff = self.clusters[clIndex][-1].get_only_num()-self.clusters[clIndex][0].get_only_num()                
                if are_scenes_joinable(diff,fps,dist,program_mode,check_mode,img1,img2,second_len_diff):
                    to_cluster_nums.append((clIndex,clIndex_temp,dist))
                    
            clIndex_temp = clIndex       
        
        self.do_scene_joining(to_cluster_nums)
        self.del_empty_clusters()       
        
    # barmelyiket barmelyikkel
    def join_near_scenes_any(self,fps,program_mode,check_mode):
        # egyelore cluster1 KOZEPSO elemeit hasonlitom ossze cluster2 REF PONTJAVAL
        # TODO: mit mivel?? pl REF pontot REF ponttal!
        # TODO: akkor joinolni csak ha a ket scene utolso + elso kepei kozott a time_diff
        to_cluster_nums = []
        for clCounter1, cluster1 in enumerate(self.clusters):
            dist_temp = Decimal('Infinity')            
            best_dist = None
            toCluster_Counter_temp = None
            cl1_len = len(cluster1)
            for clCounter2, cluster2 in enumerate(self.clusters):
                dist = cluster1[int(math.floor(cl1_len/2))].get_distance(self.get_ref_point(cluster2))
                if dist < dist_temp:
                    toCluster_Counter_temp = clCounter2
                    best_dist = dist
                dist_temp = dist
            # ha az osszerakando 2 scene kozotti tav kisebb mint a minimum scenek kozitti tav treshold, joining lesz
            if (clCounter1 != toCluster_Counter_temp):                
                diff1 = abs(self.clusters[clCounter1][0].get_only_num()-self.clusters[toCluster_Counter_temp][-1].get_only_num())
                diff2 = abs(self.clusters[clCounter1][-1].get_only_num()-self.clusters[toCluster_Counter_temp][0].get_only_num())
                diff = min(diff1,diff2)
                second_len_diff = self.clusters[clCounter1][-1].get_only_num()-self.clusters[clCounter1][0].get_only_num()
                if are_scenes_joinable(diff,fps,best_dist,program_mode,check_mode):
                    # mit, hova, tavolsaguk (dist)
                    to_cluster_nums.append((clCounter1,toCluster_Counter_temp,best_dist))
        
        self.do_scene_joining(to_cluster_nums)
        self.del_empty_clusters()
                
    def do_scene_joining(self,to_cluster_nums):
        for t in sorted(to_cluster_nums, key= lambda t: t[0], reverse=True):
            # to_cluster_nums[which#, where#, dist]
            clMoveFrom = t[0]
            clAddTo = t[1]
            # kipopolas elott berakok egy ures clustert h ne boruljanak a lista helyek, majd a vegen ureseket torlom
            self.clusters.insert(clMoveFrom,[])
            # ureset betettem igy eggyel tavolabbit kell popolni
            clToMove = self.clusters.pop(clMoveFrom+1)
            self.clusters[clAddTo].extend(clToMove)    