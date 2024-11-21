import os
import json
import boto3
import time
import math
import base64
import ffmpeg
import logging
import shutil
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
kinesisvideo = boto3.client('kinesisvideo')

def main():
    logger.info('frame_extraction started')

    # 设置 FFmpeg 和 FFprobe 的路径
    ffmpeg_binary_path = '/usr/bin/ffmpeg'
    ffprobe_binary_path = '/usr/bin/ffprobe'

    # 创建临时目录
    tmp_dir = '/tmp'
    os.makedirs(tmp_dir, exist_ok=True)

    # 复制 FFmpeg 和 FFprobe 到可写目录
    shutil.copy(ffmpeg_binary_path, os.path.join(tmp_dir, 'ffmpeg'))
    shutil.copy(ffprobe_binary_path, os.path.join(tmp_dir, 'ffprobe'))
    os.chmod(os.path.join(tmp_dir, 'ffmpeg'), 0o755)
    os.chmod(os.path.join(tmp_dir, 'ffprobe'), 0o755)

    # 更新环境变量 PATH
    current_path = os.environ.get('PATH', '')
    os.environ['PATH'] = tmp_dir + os.pathsep + current_path

    # 从环境变量中提取参数
    connection_id = os.environ.get('connection_id')
    video_analysis_lambda = os.environ.get('video_analysis_lambda')
    user_id = os.environ.get('user_id')
    video_source_type = os.environ.get('video_source_type')
    video_source_content = os.environ.get('video_source_content')
    video_upload_bucket_name = os.environ.get('video_upload_bucket_name')
    video_info_bucket_name = os.environ.get('video_info_bucket_name')
    frequency = int(os.environ.get('frequency'))
    list_length = int(os.environ.get('list_length'))
    interval = float(os.environ.get('interval'))
    duration = int(os.environ.get('duration'))
    image_size = os.environ.get('image_size')
    system_prompt = os.environ.get('system_prompt')
    user_prompt = os.environ.get('user_prompt')
    model_id = os.environ.get('model_id')
    temperature = float(os.environ.get('temperature'))
    top_p = float(os.environ.get('top_p'))
    top_k = int(os.environ.get('top_k'))
    max_tokens = int(os.environ.get('max_tokens'))

    logger.info('Parameters: connection_id={}, video_analysis_lambda={}, user_id={}, video_source_type={}, video_source_content={}'.format(
        connection_id, video_analysis_lambda, user_id, video_source_type, video_source_content))

    # KVS 帧提取
    if video_source_type == 'kvs':
        extract_frames_from_kvs(tmp_dir, frequency, list_length, interval, duration, image_size,
                                 video_source_content, video_info_bucket_name, user_id,
                                 video_analysis_lambda, system_prompt, user_prompt, model_id,
                                 temperature, top_p, top_k, max_tokens, connection_id, video_source_type)

    # S3 帧提取
    elif video_source_type == 's3':
        extract_frames_from_s3(tmp_dir, video_upload_bucket_name, video_source_content,
                           video_info_bucket_name, user_id, frequency, list_length,
                           interval, duration, image_size, video_analysis_lambda,
                           system_prompt, user_prompt, model_id, temperature, top_p,
                           top_k, max_tokens, connection_id, video_source_type)

def extract_frames_from_kvs(tmp_dir, frequency, list_length, interval, duration, image_size,
                            video_source_content, video_info_bucket_name, user_id,
                            video_analysis_lambda, system_prompt, user_prompt, model_id,
                            temperature, top_p, top_k, max_tokens, connection_id, video_source_type):

    task_timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    cycle_limit = int(duration / frequency)
    cycle_count = 0
    gap_time = list_length * interval + 4

    # 获取 KVS 信息
    kvs_endpoint = kinesisvideo.get_data_endpoint(
        StreamName=video_source_content,
        APIName='GET_IMAGES'
    ).get('DataEndpoint')

    kinesis_video_archived_media = boto3.client('kinesis-video-archived-media', endpoint_url=kvs_endpoint)

    try:
        while cycle_count < cycle_limit:
            timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=gap_time)

            if image_size != 'raw':
                width, height = image_size.split('*')
                frame_response = kinesis_video_archived_media.get_images(
                    StreamName=video_source_content,
                    ImageSelectorType='SERVER_TIMESTAMP',
                    SamplingInterval=int(interval * 1000),
                    StartTimestamp=start_time,
                    EndTimestamp=end_time,
                    Format='JPEG',
                    WidthPixels=int(width),
                    HeightPixels=int(height)
                )
            else:
                frame_response = kinesis_video_archived_media.get_images(
                    StreamName=video_source_content,
                    ImageSelectorType='SERVER_TIMESTAMP',
                    SamplingInterval=int(interval * 1000),
                    StartTimestamp=start_time,
                    EndTimestamp=end_time,
                    Format='JPEG'
                )

            image_contents_raw = [image['ImageContent'] for image in frame_response['Images'] if 'ImageContent' in image]
            image_files_raw = image_contents_raw[-1 * list_length:]

            for index, image_file_raw in enumerate(image_files_raw):
                with open(os.path.join(tmp_dir, f'{timestamp}_{index}.jpg'), "wb") as image_file:
                    image_file.write(base64.decodebytes(bytes(image_file_raw, 'utf-8')))

            image_files = [f for f in os.listdir(tmp_dir) if f.endswith('.jpg')]
            task_id = f'task_{task_timestamp}'
            image_folder = f'{video_source_type}_extract_{timestamp}_{start_time}'
            image_path = f'{user_id}/{task_id}/{image_folder}'

            for image_file in image_files:
                file_path = os.path.join(tmp_dir, image_file)
                object_key = f'{image_path}/{image_file}'
                s3.upload_file(file_path, video_info_bucket_name, object_key)
                logger.info(f'Successfully uploaded {image_file} to {video_info_bucket_name}/{object_key}')

            for image_file in image_files:
                os.remove(os.path.join(tmp_dir, image_file))

            analysis_request = {
                'system_prompt': system_prompt,
                'user_prompt': user_prompt,
                'model_id': model_id,
                'temperature': temperature,
                'top_p': top_p,
                'top_k': top_k,
                'max_tokens': max_tokens,
                'image_path': image_path,
                'start_time': start_time.strftime('%Y-%m-%d-%H:%M:%S'),
                'user_id': user_id,
                'task_id': task_id,
                'video_source_type': video_source_type,
                'video_source_content': video_source_content,
                'connection_id': connection_id
            }

            cycle_count += 1
            if cycle_count >= cycle_limit:
                analysis_request.update({'tag': 'end'})

            logger.info(f'Analysis request: {analysis_request}')
            lambda_client.invoke(
                FunctionName=video_analysis_lambda,
                InvocationType='Event',
                Payload=bytes(json.dumps(analysis_request), encoding='utf-8')
            )

            time.sleep(frequency)

    except Exception:
        logger.exception('Exception during KVS frame extraction')

def extract_frames_from_s3(tmp_dir, video_upload_bucket_name, video_source_content,
                           video_info_bucket_name, user_id, frequency, list_length,
                           interval, duration, image_size, video_analysis_lambda,
                           system_prompt, user_prompt, model_id, temperature, top_p,
                           top_k, max_tokens, connection_id, video_source_type):

    s3.download_file(video_upload_bucket_name, video_source_content, '/tmp/video.mp4')
    original_stream = ffmpeg.input('/tmp/video.mp4')

    try:
        probe = ffmpeg.probe('/tmp/video.mp4')
        original_stream_duration = math.floor(float(probe['format']['duration']))
        task_timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        start_time = 0

        while start_time < duration and start_time < original_stream_duration:
            start_time_trim = start_time
            end_time_trim = start_time + list_length * interval

            stream = ffmpeg.trim(original_stream, start=start_time_trim, end=end_time_trim)

            if image_size != 'raw':
                width, height = image_size.split('*')
                stream = ffmpeg.filter(stream, 'scale', w=width, h=height)

            stream = ffmpeg.filter(stream, 'fps', f'1/{interval}')
            timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            stream = ffmpeg.output(stream, os.path.join(tmp_dir, f'{timestamp}_%02d.jpg'), vsync='vfr', qscale=2, f='image2')

            ffmpeg.run(stream, overwrite_output=True)

            image_files = [f for f in os.listdir(tmp_dir) if f.endswith('.jpg')]
            task_id = f'task_{task_timestamp}'
            image_folder = f'{video_source_type}_extract_{timestamp}_{start_time}'
            image_path = f'{user_id}/{task_id}/{image_folder}'

            for image_file in image_files:
                file_path = os.path.join(tmp_dir, image_file)
                object_key = f'{image_path}/{image_file}'
                s3.upload_file(file_path, video_info_bucket_name, object_key)
                logger.info(f'Successfully uploaded {image_file} to {video_info_bucket_name}/{object_key}')

            for image_file in image_files:
                os.remove(os.path.join(tmp_dir, image_file))

            analysis_request = {
                'system_prompt': system_prompt,
                'user_prompt': user_prompt,
                'model_id': model_id,
                'temperature': temperature,
                'top_p': top_p,
                'top_k': top_k,
                'max_tokens': max_tokens,
                'image_path': image_path,
                'start_time': start_time,
                'user_id': user_id,
                'task_id': task_id,
                'video_source_type': video_source_type,
                'video_source_content': video_source_content,
                'connection_id': connection_id
            }

            start_time += frequency

            if start_time >= duration or start_time >= original_stream_duration:
                analysis_request.update({'tag': 'end'})

            logger.info(f'Analysis request: {analysis_request}')
            lambda_client.invoke(
                FunctionName=video_analysis_lambda,
                InvocationType='Event',
                Payload=bytes(json.dumps(analysis_request), encoding='utf-8')
            )

    except Exception:
        logger.exception('Exception during S3 frame extraction')

if __name__ == "__main__":
    main()
