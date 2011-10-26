@echo off
rmdir /S video_frames
mkdir video_frames
ffmpeg -i %1 -r %2 -an -f image2 video_frames/img%%07d.jpg