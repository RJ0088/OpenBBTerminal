import json

import pandas as pd
import pytest
from pycoingecko import CoinGeckoAPI

from openbb_terminal.cryptocurrency.cryptocurrency_helpers import (
    read_data_file,
    _load_coin_map,
    plot_chart,
    load,
    load_ta_data,
    prepare_all_coins_df,
    load_coins_list,
    _create_closest_match_df,
)

# pylint: disable=unused-import

base = "openbb_terminal.cryptocurrency."


def test_load_coin_map():
    with pytest.raises(TypeError):
        _load_coin_map("test.test")


def test_read_data_file(recorder):
    file = read_data_file("coinbase_gecko_map.json")

    recorder.capture(file)


def test_read_data_file_invalid():
    with pytest.raises(TypeError):
        read_data_file("sample.bad")


def test_load_coins_list(recorder):
    value = load_coins_list("coinbase_gecko_map.json", True)

    recorder.capture(value)


def test_load_coins_list_invalud():
    with pytest.raises(TypeError):
        load_coins_list("bad.bad")


def test_create_closet_match_df(recorder):
    df = pd.DataFrame({"id": ["btc", "eth"], "index": [1, 2]})
    value = _create_closest_match_df("btc", df, 5, 0.2)

    recorder.capture(value)


@pytest.mark.parametrize(
    "coin, interval, source",
    [
        ("badcoin", "1day", "cg"),
        ("BTC", "1hour", "cg"),
        ("BTC", "1hour", "cp"),
        ("BTC", "1hour", "cp"),
    ],
)
def test_load_none(coin, interval, source):
    assert load("BTC", vs=coin, interval=interval, source=source) == (
        None,
        None,
        None,
        None,
        None,
        None,
    )


@pytest.mark.parametrize(
    "coin, load_ta", [("BTC", True), ("ZTH", False), ("BTC", False)]
)
def test_load_cg(coin, load_ta):
    load(coin, source="cg", should_load_ta_data=load_ta)


def test_load_cg_invalid():
    load("ZTH", source="cg")


@pytest.fixture(name="get_bitcoin")
def fixture_get_bitcoin(mocker):
    # pylint: disable=unused-argument
    mock_load = mocker.patch(
        base
        + "due_diligence.pycoingecko_model.CoinGeckoAPI.get_coin_market_chart_by_id"
    )

    with open(
        "tests/openbb_terminal/cryptocurrency/json/test_cryptocurrency_helpers/btc_usd_test_data.json",
        encoding="utf8",
    ) as f:
        sample_return = json.load(f)
    mock_load.return_value = sample_return
    coin, _, symbol, _, _, _ = load(coin="BTC", source="cp")
    return coin, symbol


# pylint: disable=R0904


@pytest.mark.vcr
def test_coin_api_load(get_bitcoin):
    """
    Mock load function through get_coin_market_chart_by_id.
    Mock returns a dict saved as .json
    """
    coin, _ = get_bitcoin

    assert coin == "btc-bitcoin"


@pytest.mark.vcr
def test_coin_api_load_df_for_ta(get_bitcoin, mocker):
    """
    Mock load function through get_coin_market_chart_by_id.
    Mock returns a dict saved as .json
    """
    mock_load = mocker.patch(
        base
        + "due_diligence.pycoingecko_model.CoinGeckoAPI.get_coin_market_chart_by_id"
    )
    _, symbol = get_bitcoin
    coin_map_df = prepare_all_coins_df().set_index("Symbol").loc[symbol.upper()].iloc[0]

    with open(
        "tests/openbb_terminal/cryptocurrency/json/test_cryptocurrency_helpers/btc_usd_test_data.json",
        encoding="utf8",
    ) as f:
        sample_return = json.load(f)

    mock_load.return_value = sample_return
    mock_return, vs = load_ta_data(
        coin_map_df=coin_map_df,
        source="cg",
        currency="usd",
        days=30,
    )
    assert mock_return.shape == (31, 4)
    assert vs == "usd"


@pytest.mark.record_stdout
@pytest.mark.vcr
def test_get_coins():
    """Test that pycoingecko retrieves the major coins"""
    coins = CoinGeckoAPI().get_coins()
    bitcoin_list = [coin["id"] for coin in coins]
    test_coins = ["bitcoin", "ethereum", "dogecoin"]
    for test in test_coins:
        assert test in bitcoin_list


@pytest.mark.vcr
@pytest.mark.record_stdout
def test_coin_chart(get_bitcoin):
    # pylint: disable=unused-argument
    _, symbol = get_bitcoin
    coin_map_df = prepare_all_coins_df().set_index("Symbol").loc[symbol.upper()].iloc[0]

    plot_chart(coin_map_df=coin_map_df, source="cg", currency="usd", days=30)
