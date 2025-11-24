from celery import shared_task
from .parser import process_feed_file
from apps.feeds.models import FeedFile

@shared_task
def process_feed_file_task(feed_id):
    feed = FeedFile.objects.get(id=feed_id)
    process_feed_file(feed)
