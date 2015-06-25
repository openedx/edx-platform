"""
Script for retiring order that went through cybersource but weren't
marked as "purchased" in the db
"""

from django.core.management.base import BaseCommand, CommandError
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

    def handle(self, *args, **options):
        "Execute the command"
        if len(args) != 1:
            raise CommandError("retire_order requires one argument: <orders file>")

        with open(args[0]) as orders_file:
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
