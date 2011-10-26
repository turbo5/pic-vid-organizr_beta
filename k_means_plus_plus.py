import random
import math

def D(point,centers):
    closest_dist=None
    for c in centers:
        #dist = math.sqrt((c[0]-point[0])**2 + (c[1]-point[1])**2)
        dist = point.get_distance(c.attributes)
        closest_dist = min(dist,closest_dist or dist+1)
    return closest_dist

def weighted_choice(items):
   """items is a list of tuples in the form (item, weight)"""
   weight_total = sum((item[1] for item in items))
   n = random.uniform(0, weight_total)
   for item, weight in items:
       if n < weight:
           return item
       n = n - weight
   return item
   
def do_kmeans_plus_plus(points,NUM_OF_CLUSTERS):
    centers=[]
    
    #1 lepes random point
    p=random.choice(points)
    centers.append(p)

    #2 lepes
    for i in range(NUM_OF_CLUSTERS-1):
        w_p=[]
        sum_d_square = sum([D(p,centers)**2 for p in points])

        for this_point in points:
            if this_point in centers:continue
            weight = D(this_point,centers)**2 / sum_d_square
            w_p.append((this_point,weight))

        new_center = weighted_choice(w_p)
        centers.append(new_center)
    
    return [[c] for c in centers]

