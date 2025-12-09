from django.core.management.base import BaseCommand

from blockchain.tasks import check_pending_transactions


class Command(BaseCommand):
    help = "Poll blockchain providers for pending sell transactions and update their status."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=25, help="Maximum transactions to check per run")

    def handle(self, *args, **options):
        limit = options["limit"]
        checked, confirmed = check_pending_transactions(limit=limit)
        self.stdout.write(self.style.SUCCESS(f"Checked {checked} transactions, confirmed {confirmed}."))

