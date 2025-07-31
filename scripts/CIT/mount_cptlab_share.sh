#!/bin/bash

nohup rclone mount cptlab_share:/disk1/share ~/mnt/cptlab_share --vfs-cache-mode full --rc --rc-no-auth -vv >>/dev/null 2>&1 &