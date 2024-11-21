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
from pathlib import Path

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
kinesisvideo = boto3.client('kinesisvideo')


def lambda_handler(event, context):
    logger.info('frame_extraction: {}'.format(event))

    # Set the path to the ffmpeg binary in the Lambda layer
    ffmpeg_binary_path = '/opt/ffmpeg'
    ffprobe_binary_path = '/opt/ffprobe'

    # Copy the ffmpeg binary to a writable directory
    tmp_dir = '/tmp'
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_ffmpeg_path = os.path.join(tmp_dir, 'ffmpeg')
    shutil.copy(ffmpeg_binary_path, tmp_ffmpeg_path)
    os.chmod(Path(tmp_ffmpeg_path), 0o755)
    tmp_ffprobe_path = os.path.join(tmp_dir, 'ffprobe')
    shutil.copy(ffprobe_binary_path, tmp_ffprobe_path)
    os.chmod(Path(tmp_ffprobe_path), 0o755)

    # Add tmp folder the PATH env var
    current_path = os.environ.get('PATH', '')
    new_path = tmp_dir + os.pathsep + current_path
    os.environ['PATH'] = new_path

    # context params
    connection_id = event['connection_id']
    video_analysis_lambda = event['video_analysis_lambda']
    user_id = event['user_id']

    # video resource params
    video_source_type = event['video_source_type']
    video_source_content = event['video_source_content']
    video_upload_bucket_name = event['video_upload_bucket_name']
    video_info_bucket_name = event['video_info_bucket_name']

    # frame extraction params
    frequency = int(event['frequency'])
    list_length = int(event['list_length'])
    interval = float(event['interval'])
    duration = int(event['duration'])
    image_size = event['image_size']

    # LLM params
    system_prompt = event['system_prompt']
    user_prompt = event['user_prompt']
    model_id = event['model_id']
    temperature = float(event['temperature'])
    top_p = float(event['top_p'])
    top_k = int(event['top_k'])
    max_tokens = int(event['max_tokens'])

    # KVS frame extraction
    if video_source_type == 'kvs':
        task_timestamp = datetime.now().strftime('%Y-%m%d-%H%M%S')
        cycle_limit = int(duration / frequency)
        cycle_count = 0
        gap_time = list_length * interval + 4

        # get kvs information
        kvs_endpoint = kinesisvideo.get_data_endpoint(
            StreamName=video_source_content,
            APIName='GET_IMAGES'
        ).get('DataEndpoint')
        kinesis_video_archived_media = boto3.client('kinesis-video-archived-media', endpoint_url=kvs_endpoint)

        # start extract frames
        while cycle_count < cycle_limit:
            timestamp = datetime.now().strftime('%Y-%m%d-%H%M%S')
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=gap_time)
            try:
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
                image_contents_raw = [image['ImageContent'] for image in frame_response['Images'] if
                                      'ImageContent' in image]

                # get image list on demand
                image_files_raw = image_contents_raw[-1 * list_length:]
                for index, image_file_raw in enumerate(image_files_raw):
                    with open(os.path.join(tmp_dir, f'{timestamp}_{index}.jpg'), "wb") as image_file:
                        image_file.write(base64.decodebytes(bytes(image_file_raw, 'utf-8')))
                        image_file.close()

                # retrieve all jpg files from current directory
                image_files = [f for f in os.listdir(tmp_dir) if f.endswith('.jpg')]

                # list all images and upload to S3
                task_id = f'task_{task_timestamp}'
                image_folder = f'{video_source_type}_extract_{timestamp}_{start_time}'
                image_path = f'{user_id}/{task_id}/{image_folder}'
                for image_file in image_files:
                    file_path = os.path.join(tmp_dir, image_file)
                    object_key = f'{image_path}/{image_file}'
                    s3.upload_file(file_path, video_info_bucket_name, object_key)
                    logger.info(f'Successfully uploaded {image_file} to {video_info_bucket_name}/{object_key}')

                # clear all images under current directory for next round extraction
                for image_file in image_files:
                    os.remove(os.path.join(tmp_dir, image_file))

                # construct request and invoke analysis lambda
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

            except kinesisvideo.exceptions.ResourceNotFoundException:
                logger.warning(f"No fragments found in the stream for cycle {cycle_count}. Skipping this cycle.")
                cycle_count += 1
            except Exception as e:
                logger.exception(f'Exception during KVS frame extraction in cycle {cycle_count}: {str(e)}')
            finally:
                time.sleep(frequency)

    # S3 frame extraction
    elif video_source_type == 's3':
        # download video file from S3
        s3.download_file(video_upload_bucket_name, video_source_content, '/tmp/video.mp4')
        original_stream = ffmpeg.input('/tmp/video.mp4')

        try:
            probe = ffmpeg.probe('/tmp/video.mp4')
            original_stream_duration = math.floor(float(probe['format']['duration']))

            task_timestamp = datetime.now().strftime('%Y-%m%d-%H%M%S')
            start_time = 0
            while start_time < duration and start_time < original_stream_duration:
                # trim video start/end time
                start_time_trim = start_time
                end_time_trim = start_time + list_length * interval
                stream = ffmpeg.trim(original_stream, start=start_time_trim, end=end_time_trim)

                # apply output scale and fps filter
                if image_size != 'raw':
                    width, height = image_size.split('*')
                    stream = ffmpeg.filter(stream, 'scale', w=width, h=height)
                stream = ffmpeg.filter(stream, 'fps', f'1/{interval}')

                # set output config
                timestamp = datetime.now().strftime('%Y-%m%d-%H%M%S')
                stream = ffmpeg.output(stream, os.path.join(tmp_dir, f'{timestamp}_%02d.jpg'), vsync='vfr', qscale=2,
                                       f='image2')

                # run ffmpeg
                ffmpeg.run(stream, overwrite_output=True)

                # retrieve all jpg files from current directory
                image_files = [f for f in os.listdir(tmp_dir) if f.endswith('.jpg')]

                # list all images and upload to S3
                task_id = f'task_{task_timestamp}'
                image_folder = f'{video_source_type}_extract_{timestamp}_{start_time}'
                image_path = f'{user_id}/{task_id}/{image_folder}'
                for image_file in image_files:
                    file_path = os.path.join(tmp_dir, image_file)
                    object_key = f'{image_path}/{image_file}'
                    s3.upload_file(file_path, video_info_bucket_name, object_key)
                    logger.info(f'Successfully uploaded {image_file} to {video_info_bucket_name}/{object_key}')

                # clear all images under current directory for next round extraction
                for image_file in image_files:
                    os.remove(os.path.join(tmp_dir, image_file))

                # construct request and invoke analysis lambda
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
