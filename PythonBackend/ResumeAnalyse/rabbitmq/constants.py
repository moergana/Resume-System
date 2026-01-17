"""
RabbitMQ related constants for exchanges, queues, and routing keys.
"""
# Upload related MQ Config constants
UPLOAD_EXCHANGE_NAME = "upload.direct"
RESUME_UPLOAD_QUEUE_NAME = "resume.upload.queue"
RESUME_UPLOAD_ROUTING_KEY = "resume.upload.routing"
JD_UPLOAD_QUEUE_NAME = "jd.upload.queue"
JD_UPLOAD_ROUTING_KEY = "jd.upload.routing"


# Resume Analyse related MQ Config constants
ANALYSE_EXCHANGE_NAME = "analyse.direct"
ANALYSE_REQUEST_QUEUE_NAME = "analyse.request.queue"
ANALYSE_REQUEST_ROUTING_KEY = "analyse.request.routing"

ANALYSE_RESULT_QUEUE_NAME = "analyse.result.queue"
ANALYSE_RESULT_ROUTING_KEY = "analyse.result.routing"


# Match related MQ Config constants
MATCH_EXCHANGE_NAME = "match.direct"
JD_MATCH_REQUEST_QUEUE_NAME = "jd.match.request.queue"
RESUME_MATCH_REQUEST_QUEUE_NAME = "resume.match.request.queue"
JD_MATCH_REQUEST_ROUTING_KEY = "jd.match.request.routing"
RESUME_MATCH_REQUEST_ROUTING_KEY = "resume.match.request.routing"

JD_MATCH_RESULT_QUEUE_NAME = "jd.match.result.queue"
JD_MATCH_RESULT_ROUTING_KEY = "jd.match.result.routing"
RESUME_MATCH_RESULT_QUEUE_NAME = "resume.match.result.queue"
RESUME_MATCH_RESULT_ROUTING_KEY = "resume.match.result.routing"


# Delete related MQ Config constants
DELETE_EXCHANGE_NAME = "delete.direct"
RESUME_DELETE_QUEUE_NAME = "resume.delete.queue"
RESUME_DELETE_ROUTING_KEY = "resume.delete.routing"
JD_DELETE_QUEUE_NAME = "jd.delete.queue"
JD_DELETE_ROUTING_KEY = "jd.delete.routing"


"""
死信交换机和死信队列常量
"""
# Analyse 相关死信交换机和死信队列常量
ANALYSE_DLX_NAME = "analyse.dlx"
ANALYSE_REQUEST_DLQ_NAME = "analyse.request.dlq"
ANALYSE_REQUEST_DLQ_ROUTING_KEY = "analyse.request.dlq.routing"
ANALYSE_RESULT_DLQ_NAME = "analyse.result.dlq"
ANALYSE_RESULT_DLQ_ROUTING_KEY = "analyse.result.dlq.routing"

# Match 相关死信交换机和死信队列常量
MATCH_DLX_NAME = "match.dlx"
MATCH_REQUEST_DLQ_NAME = "match.request.dlq"
MATCH_REQUEST_DLQ_ROUTING_KEY = "match.request.dlq.routing"
MATCH_RESULT_DLQ_NAME = "match.result.dlq"
MATCH_RESULT_DLQ_ROUTING_KEY = "match.result.dlq.routing"

# Delete 相关死信交换机和死信队列常量
DELETE_DLX_NAME = "delete.dlx"
DELETE_DLQ_NAME = "delete.dlq"
DELETE_DLQ_ROUTING_KEY = "delete.dlq.routing"
