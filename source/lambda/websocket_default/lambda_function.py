import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info('on default: {}'.format(event))

    return {
        'statusCode': 200,
        'body': 'Default route'
    }
