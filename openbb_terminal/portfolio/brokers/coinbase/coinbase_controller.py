"""Coinbase Controller"""
__docformat__ = "numpy"

# pylint: disable=R0904, C0302, W0622
import argparse
import logging
from typing import List

from prompt_toolkit.completion import NestedCompleter

from openbb_terminal import feature_flags as obbff
from openbb_terminal.decorators import log_start_end
from openbb_terminal.helper_funcs import (
    EXPORT_ONLY_RAW_DATA_ALLOWED,
    check_positive,
    parse_known_args_and_warn,
)
from openbb_terminal.menu import session
from openbb_terminal.parent_classes import BaseController
from openbb_terminal.portfolio.brokers.coinbase import coinbase_view
from openbb_terminal.rich_config import console, MenuText

logger = logging.getLogger(__name__)


class CoinbaseController(BaseController):
    """Coinbase Controller class"""

    CHOICES_COMMANDS = ["account", "history", "orders", "deposits"]

    order_sortby = [
        "product_id",
        "side",
        "price",
        "size",
        "type",
        "created_at",
        "status",
    ]
    deposit_sort = [
        "created_at",
        "amount",
    ]
    PATH = "/portfolio/bro/cb/"

    def __init__(self, queue: List[str] = None):
        """Constructor"""
        super().__init__(queue)

        if session and obbff.USE_PROMPT_TOOLKIT:
            choices: dict = {c: {} for c in self.controller_choices}
            choices["orders"]["-s"] = {c: None for c in self.order_sortby}
            choices["orders"]["--sortby"] = {c: None for c in self.order_sortby}
            choices["deposits"]["-s"] = {c: None for c in self.deposit_sort}
            choices["deposits"]["--sortby"] = {c: None for c in self.deposit_sort}
            self.completer = NestedCompleter.from_nested_dict(choices)

    def print_help(self):
        """Print help"""
        mt = MenuText("portfolio/bro/cb/")
        mt.add_cmd("account")
        mt.add_cmd("history")
        mt.add_cmd("deposits")
        mt.add_cmd("orders")
        console.print(text=mt.menu_text, menu="Portfolio - Brokers - Coinbase")

    @log_start_end(log=logger)
    def call_account(self, other_args):
        """Process account command"""
        parser = argparse.ArgumentParser(
            prog="account",
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="Display info about your trading accounts on Coinbase",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Flag to display all your account",
            dest="all",
            default=False,
        )
        parser.add_argument(
            "-c",
            "--currency",
            default="USD",
            type=str,
            dest="currency",
            help="Currency to display value in.",
        )

        if other_args and other_args[0][0] != "-":
            other_args.insert(0, "--acc")

        ns_parser = parse_known_args_and_warn(
            parser, other_args, export_allowed=EXPORT_ONLY_RAW_DATA_ALLOWED
        )

        if ns_parser:
            coinbase_view.display_account(
                currency=ns_parser.currency,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_history(self, other_args):
        """Process account command"""
        parser = argparse.ArgumentParser(
            prog="history",
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="Display account history",
        )
        parser.add_argument(
            "-a",
            "--acc",
            dest="account",
            help="Symbol of coin of account or id",
            type=str,
            default="BTC",
            required=False,
        )
        parser.add_argument(
            "-l",
            "--limit",
            dest="limit",
            help="Limit parameter.",
            default=20,
            type=check_positive,
        )

        if other_args and other_args[0][0] != "-":
            other_args.insert(0, "--acc")

        ns_parser = parse_known_args_and_warn(
            parser, other_args, export_allowed=EXPORT_ONLY_RAW_DATA_ALLOWED
        )

        if ns_parser:
            coinbase_view.display_history(
                ns_parser.account, ns_parser.export, ns_parser.limit
            )

    @log_start_end(log=logger)
    def call_orders(self, other_args):
        """Process orders command"""
        parser = argparse.ArgumentParser(
            prog="orders",
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="List your current open orders",
        )
        parser.add_argument(
            "-l",
            "--limit",
            dest="limit",
            help="Limit parameter.",
            default=20,
            type=check_positive,
        )
        parser.add_argument(
            "-s",
            "--sort",
            dest="sortby",
            type=str,
            help="Sort by given column. Default: created_at",
            default="created_at",
            choices=self.order_sortby,
        )
        parser.add_argument(
            "--descend",
            action="store_false",
            help="Flag to sort in descending order (lowest first)",
            dest="descend",
            default=False,
        )
        if other_args and other_args[0][0] != "-":
            other_args.insert(0, "--acc")

        ns_parser = parse_known_args_and_warn(
            parser, other_args, export_allowed=EXPORT_ONLY_RAW_DATA_ALLOWED
        )

        if ns_parser:
            coinbase_view.display_orders(
                ns_parser.limit, ns_parser.sortby, ns_parser.descend, ns_parser.export
            )

    @log_start_end(log=logger)
    def call_deposits(self, other_args):
        """Process deposits command"""
        parser = argparse.ArgumentParser(
            prog="deposits",
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="Display a list of deposits for your account.",
        )
        parser.add_argument(
            "-t",
            "--type",
            dest="type",
            type=str,
            help="Deposit type. Either: internal_deposits (transfer between portfolios) or deposit",
            default="deposit",
            choices=["internal_deposit", "deposit"],
        )
        parser.add_argument(
            "-l",
            "--limit",
            dest="limit",
            help="Limit parameter.",
            default=20,
            type=check_positive,
        )
        parser.add_argument(
            "-s",
            "--sort",
            dest="sortby",
            type=str,
            help="Sort by given column. Default: created_at",
            default="created_at",
            choices=self.deposit_sort,
        )
        parser.add_argument(
            "--descend",
            action="store_false",
            help="Flag to sort in descending order (lowest first)",
            dest="descend",
            default=False,
        )
        ns_parser = parse_known_args_and_warn(
            parser, other_args, export_allowed=EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            coinbase_view.display_deposits(
                ns_parser.limit,
                ns_parser.sortby,
                ns_parser.type,
                ns_parser.descend,
                ns_parser.export,
            )
