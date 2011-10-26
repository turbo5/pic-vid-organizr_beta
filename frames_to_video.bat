@echo off
ffmpeg -r %1 -f image2 -i video_frames/img%%07d.jpg %2