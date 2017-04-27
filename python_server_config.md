# Server Install

## Install Python 3.5

#### Login as ROOT
sudo su - root

#### Get source code for required version
cd /usr/src
wget https://www.python.org/ftp/python/3.5.3/Python-3.5.3.tgz
tar xzf Python-3.5.3.tgz
cd Python-3.5.3

#### Linux Dependencies

yum install openssl-devel
yum install zlib-devel bzip2-devel sqlite sqlite-devel openssl-devel

#### Configure and Compile as "ALTINSTALL" 
./configure
make altinstall

#### Test
python3.5 -V
pip3.5 -V

ls -l /usr/local/bin
(shows location of alternative, newly installed Python)

#### Install pyMySQL Library

pip3.5 install pymysql

## Setup the BotUser

useradd botuser


## Install GIT ##

yum install git


## Setup Bot ##
su - botuser

git clone https://github.com/edbullen/NLPBot.git
cd NLPBot


## Logon as MySQL Linux User

ctrl-D
su - oracle

mysql -u root -p


<See README.MD for Database Setup>


ctrl-D

## Logon as botuser

su - botuser


cd NLPBot/config
echo "mySecret" > ./.key
chmod 400 .key

cd ..
python3.5 pwdutil.py -s TheBotDatabasePassword

#### Validate Database Connectivity

python3.5 pingDB.py

## Start BotServer ##

nohup python3.5 botserver.py &

## Local Client Connect ##

python3.5 simpleclient.py -a localhost -p 9999


