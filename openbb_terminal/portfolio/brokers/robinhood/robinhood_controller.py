"""Robinhood Controller"""
__docformat__ = "numpy"

import argparse
import logging
from typing import List

from prompt_toolkit.completion import NestedCompleter

from openbb_terminal.decorators import check_api_key
from openbb_terminal import feature_flags as obbff
from openbb_terminal.decorators import log_start_end
from openbb_terminal.helper_funcs import (
    EXPORT_ONLY_RAW_DATA_ALLOWED,
    parse_known_args_and_warn,
)
from openbb_terminal.menu import session
from openbb_terminal.parent_classes import BaseController
from openbb_terminal.portfolio.brokers.robinhood import (
    robinhood_model,
    robinhood_view,
)
from openbb_terminal.rich_config import console, MenuText

logger = logging.getLogger(__name__)


class RobinhoodController(BaseController):

    CHOICES_COMMANDS = ["holdings", "history", "login"]
    valid_span = ["day", "week", "month", "3month", "year", "5year", "all"]
    valid_interval = ["5minute", "10minute", "hour", "day", "week"]
    PATH = "/portfolio/bro/rh/"

    def __init__(self, queue: List[str] = None):
        """Constructor"""
        super().__init__(queue)

        if session and obbff.USE_PROMPT_TOOLKIT:
            choices: dict = {c: {} for c in self.controller_choices}
            choices["history"]["-i"] = {c: None for c in self.valid_interval}
            choices["history"]["--interval"] = {c: None for c in self.valid_interval}
            choices["history"]["-s"] = {c: None for c in self.valid_span}
            choices["history"]["--span"] = {c: None for c in self.valid_span}
            self.completer = NestedCompleter.from_nested_dict(choices)

    def print_help(self):
        """Print help"""
        mt = MenuText("portfolio/bro/rh/")
        mt.add_cmd("login")
        mt.add_raw("\n")
        mt.add_cmd("holdings")
        mt.add_cmd("history")
        console.print(text=mt.menu_text, menu="Portfolio - Brokers - Robinhood")

    @log_start_end(log=logger)
    @check_api_key(["RH_USERNAME", "RH_PASSWORD"])
    def call_login(self, _):
        """Process login"""
        robinhood_model.login()

    @log_start_end(log=logger)
    def call_holdings(self, other_args: List[str]):
        """Process holdings command"""
        parser = argparse.ArgumentParser(
            prog="holdings",
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="Display info about your trading accounts on Robinhood",
        )
        ns_parser = parse_known_args_and_warn(
            parser, other_args, export_allowed=EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            robinhood_view.display_holdings(export=ns_parser.export)

    @log_start_end(log=logger)
    def call_history(self, other_args: List[str]):
        """Process history command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="history",
            description="""Historical Portfolio Info""",
        )
        parser.add_argument(
            "-s",
            "--span",
            dest="span",
            type=str,
            choices=self.valid_span,
            default="3month",
            help="Span of historical data",
        )
        parser.add_argument(
            "-i",
            "--interval",
            dest="interval",
            default="day",
            choices=self.valid_interval,
            type=str,
            help="Interval to look at portfolio",
        )
        ns_parser = parse_known_args_and_warn(
            parser, other_args, export_allowed=EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            robinhood_view.display_historical(
                interval=ns_parser.interval,
                span=ns_parser.span,
                export=ns_parser.export,
            )
