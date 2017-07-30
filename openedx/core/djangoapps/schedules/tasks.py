from celery import task

@task
def send_email_batch(email_batch):
    email_batch.send()
    return 'foo'
