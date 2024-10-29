import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info('get_kvs_streaming_url: {}'.format(event))
    stream_name = event.get('stream_name')

    if not stream_name:
        return {
            'statusCode': 400,
            'body': 'Missing stream_name in request'
        }

    kinesisvideo = boto3.client("kinesisvideo")
    response = kinesisvideo.get_data_endpoint(
        StreamName=stream_name,
        APIName="GET_HLS_STREAMING_SESSION_URL"
    )
    endpoint_url = response.get("DataEndpoint")
    kinesis_video_archived_media = boto3.client('kinesis-video-archived-media', endpoint_url=endpoint_url)

    try:
        response = kinesis_video_archived_media.get_hls_streaming_session_url(
            StreamName=stream_name,
            PlaybackMode='LIVE',
            ContainerFormat='FRAGMENTED_MP4',
            DiscontinuityMode='ALWAYS',
            DisplayFragmentTimestamp='ALWAYS',
            Expires=3600
        )
        streaming_url = response['HLSStreamingSessionURL']
    except Exception:
        logger.exception('Failed to get KVS streaming url')
        return {
            'statusCode': 500,
            'body': 'Failed to get KVS streaming url'
        }

    return {
        'statusCode': 200,
        'action':'get_kvs_streaming_url',
        'body': json.dumps({
            'streaming_url': streaming_url
        })
    }
