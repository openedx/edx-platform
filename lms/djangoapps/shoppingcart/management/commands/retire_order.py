"""
Script for retiring order that went through cybersource but weren't
marked as "purchased" in the db
"""

from django.core.management.base import BaseCommand
from shoppingcart.models import Order
from shoppingcart.exceptions import UnexpectedOrderItemStatus, InvalidStatusToRetire


class Command(BaseCommand):
    """
    Retire orders that went through cybersource but weren't updated
    appropriately in the db
    """
    help = """
    Retire orders that went through cybersource but weren't updated appropriately in the db.
    Takes a file of orders to be retired, one order per line
    """

    def add_arguments(self, parser):
        parser.add_argument('file_name')

    def handle(self, *args, **options):
        """Execute the command"""

        with open(options['file_name']) as orders_file:
            order_ids = [int(line.strip()) for line in orders_file.readlines()]

        orders = Order.objects.filter(id__in=order_ids)

        for order in orders:
            old_status = order.status
            try:
                order.retire()
            except (UnexpectedOrderItemStatus, InvalidStatusToRetire) as err:
                print "Did not retire order {order}: {message}".format(
                    order=order.id, message=err.message
                )
            else:
                print "retired order {order_id} from status {old_status} to status {new_status}".format(
                    order_id=order.id,
                    old_status=old_status,
                    new_status=order.status,
                )
