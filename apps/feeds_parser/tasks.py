from celery import shared_task
from .parser import process_feed_file

@shared_task
def process_feed_file_task(feed_id):
    """
    Celery задача для обработки фида по его ID.
    """
    process_feed_file(feed_id)
