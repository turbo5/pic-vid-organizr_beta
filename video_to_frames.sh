#!/bin/bash
if [ -z "$1" ]; then
    echo usage: not enough parameters
    exit
fi
if [ -z "$2" ]; then
    frames=1;
else
    frames=$2;
fi
if [ -z "$3" ]; then
    repeat=1;
else
    repeat=$3;
fi
rmdir -rf video_frames	
mkdir video_frames
ffmpeg -i $1 -r $frames -an -f image2 video_frames/img%07d.jpg
