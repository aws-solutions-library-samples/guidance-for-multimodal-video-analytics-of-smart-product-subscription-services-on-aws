import csv
import boto3
from datetime import datetime

# 读取configure.csv文件
def read_config(config_file):
    config = {}
    with open(config_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            config[row[0]] = row[1]
    return config

# 定义config_file变量
config_file = '/home/ubuntu/kvs_configuration_tutorial/configure.csv'
config = read_config(config_file)

# 获取access_key、secret_key、stream_name和aws_region
access_key = config['access_key']
secret_key = config['secret_key']
stream_name = config['stream_name']
aws_region = config['aws_region']

# 创建会话并提供凭证和区域
session = boto3.Session(
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name=aws_region
)

# 使用会话创建KinesisVideo客户端
kvs_client = session.client('kinesisvideo')

# 获取KVS端点
endpoint = kvs_client.get_data_endpoint(StreamName=stream_name,
                                        APIName='GET_HLS_STREAMING_SESSION_URL')
kvs_data_endpoint = endpoint["DataEndpoint"]
print(f"KVS Data Endpoint: {kvs_data_endpoint}")

# 使用会话创建 Kinesis Video Archived Media 客户端
kvam_client = session.client('kinesis-video-archived-media',
                             endpoint_url=kvs_data_endpoint)

# 获取 HLS 流播放 URL
try:
    response = kvam_client.get_hls_streaming_session_url(
        StreamName=stream_name,
        PlaybackMode='LIVE',
        Expires=43200  # 有效期 12 小时 (43200 秒)
    )
    print(f"HLS Streaming Session URL: {response['HLSStreamingSessionURL']}")


    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 打开 HLS_Url.csv 文件并写入 HLS 流播放 URL 和当前时间
    with open('/home/ubuntu/kvs_configuration_tutorial/HLS_Url.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['HLS_Url', response['HLSStreamingSessionURL']])
        writer.writerow(['Generation_Time', current_time])
    print("The url and time have been written to the file！")

except Exception as e:
    print(f"Error: {e}")
