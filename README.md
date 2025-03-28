# For developers who modify inference apps.

We provide inference apps as CGI program of web server.
There are five apps as follows.

|  inference_type  |  inference name  |
| ---- | ---- |
|  1  |  app_car_detection  |
|  2  |  app_intersection  |
|  3  |  app_self_direction  |
|  4  |  app_opponent_direction  |
|  5  |  app_signal_detection  |

Please develop each application by following steps.

1. Clone repository
```
$ git clone https://github.com/dashcamProjects/hantaAI.git
```

2. Modify each application

Each app is located at following path. Please just edit <inference_name>.py.
```
hantaAI/cgi-bin/lib/<inference_name>/<inference_name>.py
```

3. Push your code to remote github repository.

4. If you replace model file (.h5, .weights), please upload it to following folder of our server.

```
ftp://www.utagoe.com/tmp/sjssol/model_develop/

server:www.utagoe.com
user:utagoe
pass:ht92z*****
```

Then please edit update_apps.sh for correct URL of modified .h5 file.

```
hantaAI/update_apps.sh
```

# Server side update.

Connect to AWS server (please change XX-XX-XX-XXX to correct address. You need to login to AWS site with utagoeinc account. Then check EC2 server name: g4dn-20191113).
```
https://aws.amazon.com/jp/console/
username: office@utagoe.com
pass: ut**********
```

```
$ ssh -i AWS/private_key.pem ec2-user@ec2-XX-XX-XX-XXX.ap-northeast-1.compute.amazonaws.com
```

Following commands update all of server side apps.

```
(If no 'hantaAI' direcgry under home directry, please git clone at first.)
$ git clone https://github.com/dashcamProjects/hantaAI.git

$ cd hantaAI

(If you updated update_apps.sh, please 'git pull' before executing following command.)
(Also, If you changed *.h5, please remove /tmp/*.h5 before executing folloing command.)

$ sudo ./update_apps.sh
```

# For test on server

Please test your modified app with following curl commands on server command line.
Make sure that you choose correct <inferene_type> from above table.
(eg. Change inference_type to '5' for 'app_signal_detection'.)

```
curl -X POST -i 'http://localhost/cgi-bin/cars.py' --data '{"id":"testmov001", "inference_type": 1, "input_dir": "inputs/testmov001", "input_file_last_no": 50, "output_file": "outputs/testmov001/cars.json", "progress_file": "outputs/testmov001/cars_status.json"}'

curl -X POST -i 'http://localhost/cgi-bin/inference.py' --data '{"id":"testmov001", "inference_type": 2, "input_dir": "inputs/testmov001/", "output_file": "outputs/testmov001/opponent_direction.json", "progress_file": "outputs/testmov001/opponent_direction_status.json", "start_frame": {"frame_no": 20, "x": 694, "y": 314, "w": 28, "h": 26}, "end_frame": {"frame_no": 33, "x": 1021, "y": 408, "w": 346, "h": 450}}'
```

Correct response must be as follows.
```
{"result": {"code": 200, "message": "", "desc": ""}}
```

Following command is also available for checking inference status.
```
curl -X POST -i 'http://localhost/cgi-bin/status.py' --data '{"id":"testmov001", "inference_type": 1}'
```
Response will be as follows. progress will be changed as it proceeds.
```
{"result": {"code": 200, "message": "", "desc": "", "progress": 28}}
```

# Error checking on server.
```
$ sudo tail -f /var/log/httpd/error_log
```
or
```
$ sudo tail -f /var/log/apache2/error.log
```

# For upload images on S3

1. certify aws account by using AWS's access_key and AWS's secret_access_key.
```
$ aws configure
```

```
AWS Access Key ID [******************]: (fill in <access_key>)
AWS Secret Access Key [******************]: (fill in <secret_key>)
Default region name [***********]: (fill in "ap-northeast-1")
Default output format [*****]: (fill in "JSON")
```

2. move to the directory which has image's folder and upload images by using this command
```
$ aws s3 cp LOCAL_FILE s3://{BUCKET_NAME}/REMOTE_PATH/ --recursive
```
