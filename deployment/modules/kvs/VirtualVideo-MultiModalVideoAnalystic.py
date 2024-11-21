import os
import subprocess
import signal
import sys
import csv

def read_config(config_file):
    config = {}
    with open(config_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            config[row[0]] = row[1]
    return config

def push_video_to_kvs(config):
    video_file = config['video_file_path']
    while True:
        try:
            # 运行 gst-launch-1.0 命令
            subprocess.run([
                "gst-launch-1.0",
                "filesrc", f"location={video_file}",
                "!", "decodebin",
                "!", "videoconvert",
                "!", "x264enc", "bframes=0", "key-int-max=35",
                "!", "video/x-h264,stream-format=avc,alignment=au,profile=baseline",
                "!", "kvssink", f"stream-name={config['stream_name']}", "storage-size=512",
                f"access-key={config['access_key']}", f"secret-key={config['secret_key']}",
                f"aws-region={config['aws_region']}"
            ], stdin=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            break

def signal_handler(sig, frame):
    print('Exiting...')
    sys.exit(0)

if __name__ == "__main__":
    config_file = '/home/ubuntu/kvs_configuration_tutorial/configure.csv'
    config = read_config(config_file)

    # 设置 GStreamer 插件路径
    os.environ["GST_PLUGIN_PATH"] = config['gst_plugin_path']

    signal.signal(signal.SIGINT, signal_handler)
    push_video_to_kvs(config)
