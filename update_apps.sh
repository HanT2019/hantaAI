#!/bin/sh
git pull;

echo "update all apps."
rm /var/www/cgi-bin/*.py
cp -r ./cgi-bin/*.py /var/www/cgi-bin/
rm /var/www/cgi-bin/lib/*.py
cp -r ./cgi-bin/lib/*.py /var/www/cgi-bin/lib/

rm -rf /var/www/cgi-bin/lib/app_*
cp -r ./cgi-bin/lib/app_* /var/www/cgi-bin/lib/

echo "update all models."

if [ ! -e /tmp/app_car_detection.h5 ]; then
  wget --no-check-certificate https://www.utagoe.com/tmp/ssol_hanta/model_prd/app_car_detection.h5 -P /tmp/
fi
cp /tmp/app_car_detection.h5 /var/www/cgi-bin/lib/app_car_detection/model_data/
rm /tmp/app_car_detection.h5

if [ ! -e /tmp/app_intersection.pth ]; then
  wget --no-check-certificate https://www.utagoe.com/tmp/ssol_hanta/model_prd/app_intersection.pth -P /tmp/
fi
cp /tmp/app_intersection.pth /var/www/cgi-bin/lib/app_intersection/inference/model_data/
rm /tmp/app_intersection.pth

if [ ! -e /tmp/app_opponent_direction.pth ]; then
  wget --no-check-certificate https://www.utagoe.com/tmp/ssol_hanta/model_prd/app_opponent_direction.pth -P /tmp/
fi
cp /tmp/app_opponent_direction.pth /var/www/cgi-bin/lib/app_opponent_direction/opponent_car/model_data/
rm /tmp/app_opponent_direction.pth

if [ ! -e /tmp/app_signal_detection.h5 ]; then
  wget --no-check-certificate https://www.utagoe.com/tmp/ssol_hanta/model_prd/app_signal_detection.h5 -P /tmp/
fi
cp /tmp/app_signal_detection.h5 /var/www/cgi-bin/lib/app_signal_detection/model_data/
rm /tmp/app_signal_detection.h5

echo "done."
