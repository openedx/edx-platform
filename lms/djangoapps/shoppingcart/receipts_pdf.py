from tempfile import NamedTemporaryFile

from InvoiceGenerator.api import Invoice, Item, Client, Provider, Creator
from InvoiceGenerator.pdf import SimpleInvoice


client = Client('Client company')
provider = Provider('My company', bank_account='2600420569/2010')
creator = Creator('John Doe')

invoice = Invoice(client, provider, creator)
invoice.currency_locale = 'en_US.UTF-8'
invoice.add_item(Item(32, 600, description="Item 1"))
invoice.add_item(Item(60, 50, description="Item 2", tax=10))
invoice.add_item(Item(50, 60, description="Item 3", tax=5))

for i in range(0, 100):
    invoice.add_item(Item(5+i, 600, description="Item %s"%(4+i), tax=50))

tmp_file = NamedTemporaryFile(delete=False)
pdf = SimpleInvoice(invoice)
print tmp_file.name
pdf.gen(tmp_file.name, generate_qr_code=True)