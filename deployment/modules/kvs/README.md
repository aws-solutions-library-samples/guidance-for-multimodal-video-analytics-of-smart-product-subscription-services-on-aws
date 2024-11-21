# Virtual Video Generator For Multi Modal Video Analytics
## 模块设计说明
模块功能：本模块用于模拟边缘侧视频采集设备，将视频流推送至Amazon Kinesis Video Stream，作为Multi Modal Video Analystic的实时数据流视频源。
AWS服务选型：
1.Amazon EC2(Graviton 2机型) Arm凭借其低功耗、低成本、扩展性好的特点，广泛被边缘侧视频采集设备采用，如树莓派、视频采集器等，AWS Graviton处理器是亚马逊自主设计的基于ARM架构的处理器，本模块选用 Graviton机型，其sdk 构建方法、代码同边缘侧视频采集设备基本类似，可以作为边缘侧开发的有效参考。
2.Amazon Kinesis Video Stream Kinesis Video Streams为实时视频流分析提供了完整的管理和处理管道,具备针对多种类型边缘设备的SDK,是物联网视频分析的有力工具。
本模块设计架构如下
![Arthitecture](kvs_configuration_tutorial/pic/VirtualVideo.png)
1.使用 t4g.medium 机型，选用 ubuntu 20.04操作系统，python 3.8,使用 gstreamer 循环对视频进行编解码，使用amazon-kinesis-video-streams-producer-sdk-cpp将视频流推送至 KVS，同时生成视频流 url给功能 3
2.Amazon KVS 进行视频存储及加密，构建视频通道
3.使用 Amazon其他云服务，如Lambda、 Bedrock等对视频进行抽帧及 AI 分析。
本模块主要实现了功能 1 及 2，为功能 3 建立通道。
## 部署说明(Global部署篇)
先决条件：
1.具备AWS Global账号
2.可获得本模块示例代码
部署流程：
### 云侧部署
#### Amazon Kinesis Video Stream 配置
登录AWS Console,进入 Amazon Kinesis Video Stream 页面,选择 视频流-创建，视频流同代码中 stream name相同，名称为 MultiModalVideoAnalytics，其余为默认配置即可，点击创建视频流
![Stream Build](kvs_configuration_tutorial/pic/1.png)
### 端侧部署
#### 1.启动 Amazon EC2
登录AWS Console,进入 Amazon EC2 页面，选择 启动新实例
![EC2](kvs_configuration_tutorial/pic/2.png)
命名该EC2，选择镜像ami-0620aa8714211d0af，机型选择 t4g.medium
![EC2 Start](kvs_configuration_tutorial/pic/3.png)
配置密钥对，网络及存储即可启动该 EC2
![Configure](kvs_configuration_tutorial/pic/4.png)
启动完成后，进入 EC2即可进行连接，用户可通过EC2 Instance Connect或ssh连接
![Connect](kvs_configuration_tutorial/pic/5.png)
#### 2. KVS-SDK编译构建
连接 EC2后，开始 KVS SDk 的编译构建
更新软件包列表
```
sudo apt update -y && sudo apt upgrade -y
```
安装构建 SDK 所需的库
```
sudo apt install -y \
  automake \
  build-essential \
  cmake \
  git \
  gstreamer1.0-plugins-base-apps \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-tools \
  gstreamer1.0-omx-generic \
  libcurl4-openssl-dev \
  libgstreamer1.0-dev \
  libgstreamer-plugins-base1.0-dev \
  liblog4cplus-dev \
  libssl-dev \
  python3-pip \
  pkg-config \
  gstreamer1.0-libav \
  gstreamer1.0-plugins-ugly
sudo pip install boto3
```
将Amazon PEM 文件复制到 /etc/ssl/cert.pem 中
```
sudo curl https://www.amazontrust.com/repository/AmazonRootCA1.pem -o /etc/ssl/AmazonRootCA1.pem
sudo chmod 644 /etc/ssl/AmazonRootCA1.pem
```
下载Kinesis Video Streams C++ Producer SDK
```
git clone https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git
```
准备构建目录
```
mkdir -p amazon-kinesis-video-streams-producer-sdk-cpp/build
cd amazon-kinesis-video-streams-producer-sdk-cpp/build
```
构建 SDK 和示例应用程序
```
sudo cmake .. -DBUILD_GSTREAMER_PLUGIN=ON -DBUILD_DEPENDENCIES=TRUE
sudo make install
```
部署模块代码 
可将代码下载到本地  选择code-Download this directory-tar.gz [代码gitlab网址](https://gitlab.aws.dev/aws-gcr-solutions/industry-assets/mfg/guidance-for-multi-modal-video-analytics/-/tree/main/kvs_configuration_tutorial)
本地打开 terminal将代码复制到 EC2
```
scp -i <path-to-pem> <path-to-guidance-for-multi-modal-video-analytics-main-kvs_configuration_tutorial.tar.gz>  ubuntu@<Public-IP-of-EC2>:/home/ubuntu/
```
ssh 到 EC2,解压缩代码
```
tar -xzvf /home/ubuntu/guidance-for-multi-modal-video-analytics-main-kvs_configuration_tutorial.tar.gz --strip-components=1
```
修改配置文件,将access_key,secret_key,aws_region进行配置
```
cd /home/ubuntu/kvs_configuration_tutorial
sudo vim configure.csv
```
## Virtual Video Generator运行
生成视频流并循环推送至 Amazon Kinesis Video Stream
```
cd /home/ubuntu/kvs_configuration_tutorial/
sudo python3 VirtualVideo-MultiModalVideoAnalystic.py
```
通过 Amazon Kinesis Video Stream console即可查看视频流
![KVS](kvs_configuration_tutorial/pic/6.png)
视频流建立后，可生成 HLS Url 以便调用该视频流
```
cd /home/ubuntu/kvs_configuration_tutorial/
sudo python3 Get_HLS_Url.py
```
输出内容举例如下
```
HLS Streaming Session URL: https://x-xxxxxxx.kinesisvideo.us-east-1.amazonaws.com/hls/v1/getHLSMasterPlaylist.m3u8?SessionToken=CiClWSpWAqix4Vu0YNQgEnTseLRrHemDdaPjszloHFr_FxIQhhTbzvNq3Dh39egtCkZiABoZq-bYUUMsJopLsw7kzXP-TbbI9_tCX7O58iIgdoVTAesira4uEeaTMl4r9P_N16xVJ3dyH4HzYF9E8Kc~
The url and time have been written to the file！
```
HLS Url 同时也被写入/home/ubuntu/kvs_configuration_tutorial/HLS_Url.csv文件中，以便读取
注意：HLS Url 链接有效期为 12 小时