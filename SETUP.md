# Environment Setup
### On Ubuntu 20.04 (Storage > 20GB)
```
// clone repository
$ sudo apt-get update
$ sudo apt-get upgrade
$ sudo apt-get install git
$ sudo git clone https://github.com/dashcamProjects/hantaAI.git
$ cd ~/hantaAI
$ sudo sh install_apps.sh

// log directory
$ sudo mkdir -p /var/log/hanta_log/old
$ sudo chown www-data:www-data /var/log/hanta_log
$ sudo chown www-data:www-data /var/log/hanta_log/old

// logrotate settings
$ sudo vi /etc/logrotate.d/hanta
// add below
/*
/var/log/hanta_log/*log {
  daily
  rotate 30
  missingok
  compress
  delaycompress
  notifempty
  dateext
  olddir /var/log/hanta_log/old
}
*/
$ sudo logrotate -dv /etc/logrotate.d/hanta

// Disable PrivateTmp
$ sudo cp /usr/lib/systemd/system/apache2.service /etc/systemd/system/
$ sudo chmod 777 /etc/systemd/system/apache2.service
$ sudo vi /etc/systemd/system/apache2.service
/*
PrivateTmp=true　→　PrivateTmp=false
*/
$ sudo systemctl daemon-reload

// install cuda
$ cd ~
$ wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
$ sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
$ sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
$ sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
$ sudo apt-get update
$ sudo apt-get -y install cuda

// system python setup
$ sudo apt-get -y install python3-pip
$ sudo pip3 install -U pip
$ sudo pip3 install -U awscli
$ sudo pip3 install boto3
$ sudo pip3 install psutil
$ sudo pip3 install setproctitle

// pyenv setup
$ cd ~/hantaAI
$ sudo sh pyenv_setup.sh
$ sudo visudo
// add following pyenv path to the secure_path as follows
// Defaults secure_path = /usr/local/pyenv/bin:/usr/local/pyenv/shims:/sbin:/bin:/usr/sbin
$ sudo su
# pyenv install 3.6.5
# pyenv global 3.6.5
# exit
$ sudo pip3 install -U pip
$ sudo pip3 install -U awscli
$ sudo pip3 install boto3
$ sudo pip3 install opencv-python
$ sudo pip3 install image
$ sudo pip3 install ffmpy
$ sudo pip3 install requests
$ sudo pip3 install h5py==2.10.0
$ sudo pip3 install tensorflow-gpu==1.14.0 --ignore-installed
$ sudo pip3 install Keras==2.3.1
$ sudo pip3 install torch==1.7.1+cu110 torchvision==0.8.2+cu110 torchaudio===0.7.2 -f https://download.pytorch.org/whl/torch_stable.html

// apache2 setup
$ sudo apt-get -y install apache2
$ sudo vi /etc/apache2/conf-available/serve-cgi-bin.conf
// replace with below
/*
<IfModule mod_alias.c>
        <IfModule mod_cgi.c>
                Define ENABLE_USR_LIB_CGI_BIN
        </IfModule>

        <IfModule mod_cgid.c>
                Define ENABLE_USR_LIB_CGI_BIN
        </IfModule>

        <IfDefine ENABLE_USR_LIB_CGI_BIN>
                ScriptAlias /cgi-bin/ /var/www/cgi-bin/
                <Directory "/var/www/cgi-bin">
                        AddHandler cgi-script .cgi .py
                        AllowOverride None
                        Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
                        Require all granted
                </Directory>
        </IfDefine>
</IfModule>
*/                                           
$ sudo vi /etc/apache2/conf-available/security.conf
// add below
/*
SetEnv AWS_ACCESS_KEY_ID "********************"
SetEnv AWS_SECRET_ACCESS_KEY "********************************"
SetEnv AWS_S3_BUCKET_NAME "*******************"
SetEnv PYENV_ROOT "/usr/local/pyenv/shims/"
*/
$ sudo a2enmod cgid
$ sudo systemctl restart apache2
```
