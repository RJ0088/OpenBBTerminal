""" Discovery Controller Module """
__docformat__ = "numpy"

import argparse
import logging
from datetime import datetime
from typing import List

from prompt_toolkit.completion import NestedCompleter

from openbb_terminal import feature_flags as obbff
from openbb_terminal.decorators import log_start_end
from openbb_terminal.helper_funcs import (
    EXPORT_ONLY_RAW_DATA_ALLOWED,
    check_int_range,
    check_non_negative,
    check_positive,
    parse_known_args_and_warn,
    valid_date,
    valid_date_in_past,
)
from openbb_terminal.menu import session
from openbb_terminal.parent_classes import BaseController
from openbb_terminal.rich_config import console, MenuText
from openbb_terminal.stocks.discovery import (
    ark_view,
    fidelity_view,
    finnhub_view,
    nasdaq_view,
    seeking_alpha_view,
    shortinterest_view,
    yahoofinance_view,
)

# pylint:disable=C0302


logger = logging.getLogger(__name__)


class DiscoveryController(BaseController):
    """Discovery Controller class"""

    CHOICES_COMMANDS = [
        "pipo",
        "fipo",
        "gainers",
        "losers",
        "ugs",
        "gtech",
        "active",
        "ulc",
        "asc",
        "ford",
        "arkord",
        "upcoming",
        "trending",
        "lowfloat",
        "hotpenny",
        "cnews",
        "rtat",
        "divcal",
    ]

    arkord_sortby_choices = [
        "date",
        "volume",
        "open",
        "high",
        "close",
        "low",
        "total",
        "weight",
        "shares",
    ]
    arkord_fund_choices = ["ARKK", "ARKF", "ARKW", "ARKQ", "ARKG", "ARKX", ""]
    cnews_type_choices = [
        nt.lower()
        for nt in [
            "Top-News",
            "On-The-Move",
            "Market-Pulse",
            "Notable-Calls",
            "Buybacks",
            "Commodities",
            "Crypto",
            "Issuance",
            "Global",
            "Guidance",
            "IPOs",
            "SPACs",
            "Politics",
            "M-A",
            "Consumer",
            "Energy",
            "Financials",
            "Healthcare",
            "MLPs",
            "REITs",
            "Technology",
        ]
    ]
    PATH = "/stocks/disc/"
    dividend_columns = [
        "Name",
        "Symbol",
        "Ex-Dividend Date",
        "Payment Date",
        "Record Date",
        "Dividend",
        "Indicated Annual Dividend",
        "Announcement Date",
    ]

    def __init__(self, queue: List[str] = None):
        """Constructor"""
        super().__init__(queue)

        if session and obbff.USE_PROMPT_TOOLKIT:
            choices: dict = {c: {} for c in self.controller_choices}
            choices["arkord"]["-s"] = {c: None for c in self.arkord_sortby_choices}
            choices["arkord"]["--sortby"] = {
                c: None for c in self.arkord_sortby_choices
            }
            choices["arkord"]["-f"] = {c: None for c in self.arkord_fund_choices}
            choices["arkord"]["--fund"] = {c: None for c in self.arkord_fund_choices}
            choices["cnews"]["-t"] = {c: None for c in self.cnews_type_choices}
            choices["cnews"]["--type"] = {c: None for c in self.cnews_type_choices}
            choices["divcal"]["-s"] = {c: None for c in self.dividend_columns}
            choices["divcal"]["--sort"] = {c: None for c in self.dividend_columns}

            self.completer = NestedCompleter.from_nested_dict(choices)

    def print_help(self):
        """Print help"""
        mt = MenuText("stocks/disc/")
        mt.add_cmd("pipo", "Finnhub")
        mt.add_cmd("fipo", "Finnhub")
        mt.add_cmd("gainers", "Yahoo Finance")
        mt.add_cmd("losers", "Yahoo Finance")
        mt.add_cmd("ugs", "Yahoo Finance")
        mt.add_cmd("gtech", "Yahoo Finance")
        mt.add_cmd("active", "Yahoo Finance")
        mt.add_cmd("ulc", "Yahoo Finance")
        mt.add_cmd("asc", "Yahoo Finance")
        mt.add_cmd("ford", "Fidelity")
        mt.add_cmd("arkord", "Cathiesark")
        mt.add_cmd("upcoming", "Seeking Alpha")
        mt.add_cmd("trending", "Seeking Alpha")
        mt.add_cmd("cnews", "Seeking Alpha")
        mt.add_cmd("lowfloat", "Fidelity")
        mt.add_cmd("hotpenny", "Shortinterest")
        mt.add_cmd("rtat", "NASDAQ Data Link")
        mt.add_cmd("divcal", "NASDAQ Data Link")
        console.print(text=mt.menu_text, menu="Stocks - Discovery")

    # TODO Add flag for adding last price to the following table
    @log_start_end(log=logger)
    def call_divcal(self, other_args: List[str]):
        """Process divcal command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="divcal",
            description="""Get dividend calendar for selected date""",
        )
        parser.add_argument(
            "-d",
            "--date",
            default=datetime.now(),
            type=valid_date,
            dest="date",
            help="Date to get format for",
        )
        parser.add_argument(
            "-s",
            "--sort",
            default=["Dividend"],
            nargs="+",
            type=str,
            help="Column to sort by",
            dest="sort",
        )
        parser.add_argument(
            "-a",
            "--ascend",
            default=False,
            action="store_true",
            help="Flag to sort in ascending order",
            dest="ascend",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-d")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, export_allowed=EXPORT_ONLY_RAW_DATA_ALLOWED, limit=10
        )
        if ns_parser:
            sort_col = " ".join(ns_parser.sort)
            if sort_col not in self.dividend_columns:
                console.print(f"{sort_col} not a valid selection for sorting.\n")
                return
            nasdaq_view.display_dividend_calendar(
                ns_parser.date.strftime("%Y-%m-%d"),
                sort_col=sort_col,
                ascending=ns_parser.ascend,
                limit=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_pipo(self, other_args: List[str]):
        """Process pipo command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="pipo",
            description="""
                Past IPOs dates. [Source: https://finnhub.io]
            """,
        )
        parser.add_argument(
            "-d",
            "--days",
            action="store",
            dest="days",
            type=check_non_negative,
            default=5,
            help="Number of past days to look for IPOs.",
        )

        parser.add_argument(
            "-s",
            "--start",
            type=valid_date_in_past,
            default=None,
            dest="start",
            help="""The starting date (format YYYY-MM-DD) to look for IPOs.
            When set, start date will override --days argument""",
        )

        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_non_negative,
            default=20,
            help="Limit number of IPOs to display.",
        )

        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            finnhub_view.past_ipo(
                num_days_behind=ns_parser.days,
                limit=ns_parser.limit,
                start_date=ns_parser.start,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_fipo(self, other_args: List[str]):
        """Process fipo command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="fipo",
            description="""
                Future IPOs dates. [Source: https://finnhub.io]
            """,
        )

        parser.add_argument(
            "-d",
            "--days",
            action="store",
            dest="days",
            type=check_non_negative,
            default=5,
            help="Number of days in the future to look for IPOs.",
        )

        parser.add_argument(
            "-s",
            "--end",
            type=valid_date,
            default=None,
            dest="end",
            help="""The end date (format YYYY-MM-DD) to look for IPOs, starting from today.
            When set, end date will override --days argument""",
        )

        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_non_negative,
            default=20,
            help="Limit number of IPOs to display.",
        )

        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )

        if ns_parser:
            finnhub_view.future_ipo(
                num_days_ahead=ns_parser.days,
                limit=ns_parser.limit,
                end_date=ns_parser.end,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_gainers(self, other_args: List[str]):
        """Process gainers command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="gainers",
            description="Print up to 25 top gainers. [Source: Yahoo Finance]",
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_int_range(1, 25),
            default=5,
            help="Limit of stocks to display.",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            yahoofinance_view.display_gainers(
                num_stocks=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_losers(self, other_args: List[str]):
        """Process losers command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="losers",
            description="Print up to 25 top losers. [Source: Yahoo Finance]",
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_int_range(1, 25),
            default=5,
            help="Limit of stocks to display.",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            yahoofinance_view.display_losers(
                num_stocks=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_ugs(self, other_args: List[str]):
        """Process ugs command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="ugs",
            description="""
                Print up to 25 undervalued stocks with revenue and earnings growth in excess of 25%.
                [Source: Yahoo Finance]
            """,
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_int_range(1, 25),
            default=5,
            help="Limit of stocks to display.",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            yahoofinance_view.display_ugs(
                num_stocks=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_gtech(self, other_args: List[str]):
        """Process gtech command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="gtech",
            description="Print up to 25 top tech stocks with revenue and earnings"
            + " growth in excess of 25%. [Source: Yahoo Finance]",
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_int_range(1, 25),
            default=5,
            help="Limit of stocks to display.",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            yahoofinance_view.display_gtech(
                num_stocks=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_active(self, other_args: List[str]):
        """Process active command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="active",
            description="""
                Print up to 25 top most actively traded intraday tickers. [Source: Yahoo Finance]
            """,
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_int_range(1, 25),
            default=5,
            help="Limit of stocks to display.",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            yahoofinance_view.display_active(
                num_stocks=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_ulc(self, other_args: List[str]):
        """Process ulc command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="ulc",
            description="""
                Print up to 25 potentially undervalued large cap stocks. [Source: Yahoo Finance]
            """,
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_int_range(1, 25),
            default=5,
            help="Limit of stocks to display.",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            yahoofinance_view.display_ulc(
                num_stocks=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_asc(self, other_args: List[str]):
        """Process asc command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="asc",
            description="""
                Print up to 25 small cap stocks with earnings growth rates better than 25%. [Source: Yahoo Finance]
            """,
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_int_range(1, 25),
            default=5,
            help="Limit of stocks to display.",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            yahoofinance_view.display_asc(
                num_stocks=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_ford(self, other_args: List[str]):
        """Process ford command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="ford",
            description="""
                Orders by Fidelity customers. Information shown in the table below
                is based on the volume of orders entered on the "as of" date shown. Securities
                identified are not recommended or endorsed by Fidelity and are displayed for
                informational purposes only. [Source: Fidelity]
            """,
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_int_range(1, 25),
            default=5,
            help="Limit of stocks to display.",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            fidelity_view.orders_view(
                num=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_arkord(self, other_args: List[str]):
        """Process arkord command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="arkord",
            description="""
                Orders by ARK Investment Management LLC - https://ark-funds.com/. [Source: https://cathiesark.com]
            """,
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_positive,
            default=10,
            help="Limit of stocks to display.",
        )
        parser.add_argument(
            "-s",
            "--sortby",
            dest="sort_col",
            choices=self.arkord_sortby_choices,
            nargs="+",
            help="Column to sort by",
            default="",
        )
        parser.add_argument(
            "-a",
            "--ascend",
            dest="ascend",
            help="Flag to sort in ascending order",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "-b",
            "--buy_only",
            dest="buys_only",
            help="Flag to look at buys only",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "-c",
            "--sell_only",
            dest="sells_only",
            help="Flag to look at sells only",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "-f",
            "--fund",
            type=str,
            default="",
            help="Filter by fund",
            dest="fund",
            choices=self.arkord_fund_choices,
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            ark_view.ark_orders_view(
                num=ns_parser.limit,
                sort_col=ns_parser.sort_col,
                ascending=ns_parser.ascend,
                buys_only=ns_parser.buys_only,
                sells_only=ns_parser.sells_only,
                fund=ns_parser.fund,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_upcoming(self, other_args: List[str]):
        # TODO: switch to nasdaq
        """Process upcoming command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="upcoming",
            description="""Upcoming earnings release dates. [Source: Seeking Alpha]""",
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_positive,
            default=1,
            help="Limit of upcoming earnings release dates to display.",
        )
        parser.add_argument(
            "-p",
            "--pages",
            action="store",
            dest="n_pages",
            type=check_positive,
            default=10,
            help="Number of pages to read upcoming earnings from in Seeking Alpha website.",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            seeking_alpha_view.upcoming_earning_release_dates(
                num_pages=ns_parser.n_pages,
                num_earnings=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_trending(self, other_args: List[str]):
        """Process trending command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="trending",
            description="""Trending news articles. [Source: Seeking Alpha]""",
        )
        parser.add_argument(
            "-i",
            "--id",
            action="store",
            dest="n_id",
            type=check_positive,
            default=-1,
            help="article ID",
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_positive,
            default=5,
            help="limit of articles being printed",
        )
        parser.add_argument(
            "-d",
            "--date",
            action="store",
            dest="s_date",
            type=valid_date,
            default=datetime.now().strftime("%Y-%m-%d"),
            help="starting date of articles",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-i")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            seeking_alpha_view.news(
                article_id=ns_parser.n_id,
                num=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_lowfloat(self, other_args: List[str]):
        """Process lowfloat command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="lowfloat",
            description="""
                Print top stocks with lowest float. LowFloat.com provides a convenient
                sorted database of stocks which have a float of under 10 million shares. Additional key
                data such as the number of outstanding shares, short interest, and company industry is
                displayed. Data is presented for the Nasdaq Stock Market, the New York Stock Exchange,
                the American Stock Exchange, and the Over the Counter Bulletin Board. [Source: www.lowfloat.com]
            """,
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_positive,
            default=5,
            help="limit of stocks to display",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            shortinterest_view.low_float(
                num=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_cnews(self, other_args: List[str]):
        """Process cnews command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="cnews",
            description="""Customized news. [Source: Seeking Alpha]""",
        )
        parser.add_argument(
            "-t",
            "--type",
            action="store",
            dest="s_type",
            choices=self.cnews_type_choices,
            default="Top-News",
            help="number of news to display",
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_positive,
            default=5,
            help="limit of news to display",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-t")

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            seeking_alpha_view.display_news(
                news_type=ns_parser.s_type,
                num=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_hotpenny(self, other_args: List[str]):
        """Process hotpenny command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="hotpenny",
            description="""
                This site provides a list of todays most active and hottest penny stocks. While not for everyone, penny
                stocks can be exciting and rewarding investments in many ways. With penny stocks, you can get more bang
                for the buck. You can turn a few hundred dollars into thousands, just by getting in on the right penny
                stock at the right time. Penny stocks are increasing in popularity. More and more investors of all age
                groups and skill levels are getting involved, and the dollar amounts they are putting into these
                speculative investments are representing a bigger portion of their portfolios.
                [Source: www.pennystockflow.com]
            """,
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_positive,
            default=5,
            help="limit of stocks to display",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            shortinterest_view.hot_penny_stocks(
                num=ns_parser.limit,
                export=ns_parser.export,
            )

    @log_start_end(log=logger)
    def call_rtat(self, other_args: List[str]):
        """Process fds command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="rtat",
            description="""
                Tracking over $30B USD/day of individual investors trades,
                RTAT gives a daily view into retail activity and sentiment for over 9,500 US traded stocks,
                ADRs, and ETPs
            """,
        )
        parser.add_argument(
            "-l",
            "--limit",
            action="store",
            dest="limit",
            type=check_positive,
            default=3,
            help="limit of days to display",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, export_allowed=EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            nasdaq_view.display_top_retail(
                n_days=ns_parser.limit, export=ns_parser.export
            )
