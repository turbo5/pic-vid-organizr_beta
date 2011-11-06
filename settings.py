import sys

GLOBAL_SLASH = '/'
if 'win' in sys.platform: 
    GLOBAL_SLASH =  "\\"
    is_win = True
else:
    is_win = False

DATE_MAX = 24*3600

# minden "ennyiedik" objektumot probal a SIFT matchelni, source es compared kepekbol
# 0 0 , 1 1 , eseten mindent mindennel, k*(k-1)/2
LESS_MATCHES_ATTEMPT_SOURCE = 1
LESS_MATCHES_ATTEMPT_COMPARED = 1

# keypoints(img1)/keypoints(img2) aranya, R, ha kicsi, pontatlan lehet a matching!
# R < 1 JO ; R > 1 ROSSZ ... telenor SIFT doksi alapjan.
# nem vagyok biztos benne h annyit ront, es hogy nekem kell-e ez a faktor..
# de leszabalyozom, lasd doku, sztem annyit nem ront a helyzeten
KeypointsRatio_low = 0.9 # JO: ne legyen ennel nagyobb (1/(0.9)^2 = 1,2345) javitas
KeypointsRatio_high = 1.2 # ROSSZ: ne legyen ennel nagyobb (1/(1.2)^2 = 0,4822) rontas

# size of thumb images - needed before making SIFT matching
# 450x300 -nal nagyobb nem ajanlott egyelore! futasido! optimalizalas TODO
THUMBS_SIZE = '400x300'

# minimum QOM value to determine if 2 images are matching while doin SIFT
QOM_minimum = 2.3

# legkevesebb ennyi szazaleknyi egyezes kell a keypontokbol, kulonben bunteto parameter
LOWEST_MATCHES_NUM = 30

# kepek szamanak ennyi szazalekat meghalado meretu klaszterbol mar lesz kivalasztott jellemzo kep
MIN_SIZE_OF_RELEVANT_CLUSTER = 0.12



######################## VIDEO ##########################

# egy scene minimum hossza (ennel rovidebbeket torlom), outlier elemek; SEC
# SCENE DELETE ESETEN
MIN_SCENE_LENGTH_MODE_SCENECUT = 0.5
MIN_SCENE_LENGTH_MODE_JOINCUT = 2.0

# minimum scene hossz, scene ujraegyesites eseten; 'length' modban. ennyi SEC alattit a mellette levo scenhez joinolok.
# SCENE JOIN ESETEN
LENGTH_TRESH_MODE_SCENECUT = 1.1
LENGTH_TRESH_MODE_JOINCUT = 2.1

# scenek (clusterek) ujraegyesitesenel ekkora tav alatt (2 cluster scene kozott) egyesitunk, ennel nagyobb eseten nem
# ugyanez a hatar szetvalasztasnal (csak ott ennel nagyobb eseten szetvalasztas)
# ket modban mukodhet, videok joinolasat vagjuk, vagy videoban sceneket
CLUSTER_DISTANCE_TRESHOLD_MODE_SCENECUT = 0.09
CLUSTER_DISTANCE_TRESHOLD_MODE_JOINCUT = 0.4
CLUSTER_DISTANCE_TRESHOLD_SIMILAR_CHECK = 0.1
# ez az a hatar, ami felett megnezzuk SIFT-el is a 2 kepet, hatha lehet a mentukon scene-t vagni
CLUSTER_DISTANCE_TRESHOLD_MODE_SCENECUT_CHECK_SIFT = 0.07
CLUSTER_DISTANCE_TRESHOLD_MODE_JOINCUT_CHECK_SIFT = 0.35

# video szegmentalas eseten; ennyi MASODPERC-en belul torteno, ket ugyanabba a clusterben levo esemenyt(kepet) egy jelenetnek veszunk
# ennel nagyobb eseten a ket kep kulon jelenetbe tartozik.
# ezek kozelito ertekek, nem pontosak!!! (ffmpeg codec pontossagan mulik)
TIMEDIFF_TRESH_MODE_SCENECUT = 1.0
TIMEDIFF_TRESH_MODE_JOINCUT = 3.0

# SIFT alapu scene egyesitesnel a minimum QoM
QOM_MINIMUM_SCENEJOIN = 2.7
# SIFT alapu scene vagasnal a maximum QoM
QOM_MINIMUM_SCENECUT = 2.3




# SECOND VALUES ARE THE MAX VALUES
EXIF_ATTRIBUTES = [
    ["EXIF Contrast"],
    ["EXIF ExposureProgram"],
    ["EXIF Flash"],
    ["EXIF LightSource"],
    ["EXIF MeteringMode"],
    ["EXIF Saturation"],
    ["EXIF SceneCaptureType"],
    ["EXIF Sharpness"],
    ["EXIF WhiteBalance"],
    ["Image Orientation"],
    ["EXIF ExposureTime",10],
    ["EXIF FNumber",22],
    ["EXIF FocalLengthIn35mmFilm",500]
    #["EXIF ISOSpeedRatings",6400]
]

# max_sum a main.py ben mert kepfuggo
max_mean = 255
max_median = 255
max_rms = 255
max_var = 127.5**2

WEIGHTS = {
    "EXIF Contrast":0.7,
    "EXIF ExposureProgram":0.6,
    "EXIF Flash":1,
    "EXIF LightSource":0.4,
    "EXIF MeteringMode":1.2,
    "EXIF Saturation":1,
    "EXIF SceneCaptureType":0.8,
    "EXIF Sharpness":1.4,
    "EXIF WhiteBalance":2,
    "Image Orientation":0.3,
    "EXIF ExposureTime":2,
    "EXIF FNumber":2,
    "EXIF FocalLengthIn35mmFilm":3,
    #"EXIF ISOSpeedRatings":2,
    "sum2":6,
    "mean":3,
    "median":2,
    "rms":3,
    "var":3
}
