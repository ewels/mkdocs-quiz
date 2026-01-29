#!/bin/bash

ffmpeg -i cli-demo.gif -movflags faststart -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" cli-demo.mp4
