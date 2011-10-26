import Image
import ImageDraw
import random
import math

WIDTH=1000
HEIGHT=700
NUM_OF_POINTS=500
NUM_OF_CLUSTERS=15

def draw_point(point, weight, color):
    draw.ellipse(((point[0]-weight,point[1]-weight),(point[0]+weight,point[1]+weight)),fill=color)

def D(point):
    closest_dist=None
    for c in centers:
        dist = math.sqrt((c[0]-point[0])**2 + (c[1]-point[1])**2)
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
#=========================================

image=Image.new('RGB',(WIDTH,HEIGHT))
draw=ImageDraw.Draw(image)
draw.rectangle( ((10,10),(WIDTH-10,HEIGHT-10)) , (155,155,155))
draw.rectangle( ((11,11),(WIDTH-11,HEIGHT-11)) , 0)

points=[]
for i in range(NUM_OF_POINTS):
    x=random.randrange(10,WIDTH-10)
    y=random.randrange(10,HEIGHT-10)
    p=(x,y)
    draw_point(p,1,(255,255,255))
    points.append(p)
    

centers=[]

#1 lepes random point
p=random.choice(points)
centers.append(p)
draw_point(p,4,255)

#2 lepes
for i in range(NUM_OF_CLUSTERS-1):
    w_p=[]
    sum_d_square = sum([D(p)**2 for p in points])
    print '==========================='

    for this_point in points:
        if this_point in centers:continue
        weight = D(this_point)**2 / sum_d_square
        #draw.text(this_point, '(%s)' % weight, (155,155,155))
        w_p.append((this_point,weight))

    #~ for x in w_p:print x
    new_center = weighted_choice(w_p)
    draw_point(new_center, 4,(255,255,0))
    centers.append(new_center)
    print new_center

image.show()
