"""
This file exposes methods to initiate a transaction synchronization from a remote
Payment Processor and the local database
"""

import pytz
from django.conf import settings
from django.core.mail.message import EmailMessage
from datetime import datetime
from django.utils.translation import ugettext as _

from .models import (
    Order,
    PaymentTransactionSync,
    PaymentTransaction,
)
from .processors import (
    synchronize_transactions
)


def perform_sync(start_date=None, end_date=None, summary_email_to=None):
    """
    This method will perform a sync from the Payment Processor to the local database in the given date ranges. If no
    dates are provided, then we will sync from the last known sync date that has been stored in our sync history
    records. If there has been no sync history yet, we will query the local database to see the first purchased
    Order and use that as the sync date.

    Note that we only do synchronizations on full days
    """

    if not start_date:
        # look in the list of synched transactions that we have already done
        start_date = PaymentTransaction.get_last_processed_date()

        if not start_date:
            order = (Order.objects.all().order_by('id'))[0]
            start_date = order.purchase_time
            print start_date

            if not start_date:
                start_date = datetime.now(pytz.UTC)

    if not end_date:
        end_date = datetime.now(pytz.UTC)

    start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # record sync operation
    sync_op = PaymentTransactionSync(
        date_range_start=start_date,
        date_range_end=start_date,
        rows_processed=0,
        rows_in_error=0,
        sync_started_at=datetime.now(pytz.UTC),
    )
    sync_op.save()

    num_processed, num_in_err, errors = synchronize_transactions(start_date, end_date)

    # note, don't commit a end_date to the sync history that is greater than the last processed
    # transaction. This is because some processors can have a lag in when they can show up in reports

    sync_op.date_range_end = end_date
    sync_op.rows_processed = num_processed
    sync_op.rows_in_error = num_in_err
    sync_op.sync_ended_at = datetime.now(pytz.UTC)

    sync_op.save()

    # lastly, send a summary email if requested
    if summary_email_to:
        subject = _("Shoppingcart Payment Processor Synchronization Report")

        message = _(
            "A synchronization of the Shoppingcart with the Payment Processor "
            "has been completed\n\n"
            "start_date = {start_date}  "
            "end_date = {end_date}  "
            "num_processed = {num_processed}  "
            "rows_in_error = {rows_in_error}"
        ).format(
            start_date=start_date,
            end_date=end_date,
            num_processed=num_processed,
            rows_in_error=num_in_err,
        )

        if errors:
            message = message + "\n\n" + _("DUMP OF ERRORS FOUND:")
            for error in errors:
                message = message + "\n\n{}".format(error)

        to_email = [summary_email_to]
        from_email = settings.PAYMENT_SUPPORT_EMAIL

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=to_email
        )
        email.send()

    return sync_op
