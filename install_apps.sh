#!/bin/sh

if [ ! -e /tmp/cgi-bin.tgz ]; then
  wget https://www.utagoe.com/tmp/ssol_hanta/sample_code/cgi-bin.tgz -P /tmp/
fi
tar zxf /tmp/cgi-bin.tgz -C /tmp/
sudo cp -r /tmp/cgi-bin/* /var/www/cgi-bin/

if [ ! -e /tmp/app_car_detection.h5 ]; then
  wget https://www.utagoe.com/tmp/ssol_hanta/model_prd/app_car_detection.h5 -P /tmp/
fi
cp /tmp/app_car_detection.h5 /var/www/cgi-bin/lib/app_car_detection/model_data/

if [ ! -e /tmp/app_intersection.pth ]; then
  wget https://www.utagoe.com/tmp/ssol_hanta/model_prd/app_intersection.pth -P /tmp/
fi
cp /tmp/app_intersection.pth /var/www/cgi-bin/lib/app_intersection/inference/model_data/

if [ ! -e /tmp/app_opponent_direction.pth ]; then
  wget https://www.utagoe.com/tmp/ssol_hanta/model_prd/app_opponent_direction.pth -P /tmp/
fi
cp /tmp/app_opponent_direction.pth /var/www/cgi-bin/lib/app_opponent_direction/opponent_car/model_data/

if [ ! -e /tmp/app_signal_detection.h5 ]; then
  wget https://www.utagoe.com/tmp/ssol_hanta/model_prd/app_signal_detection.h5 -P /tmp/
fi
cp /tmp/app_signal_detection.h5 /var/www/cgi-bin/lib/app_signal_detection/model_data/

echo "done."
