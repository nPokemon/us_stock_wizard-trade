import pandas as pd
import plotly.graph_objects as go
from us_stock_wizard.database.db_utils import DbTable, StockDbUtils


class StockPlot:
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker

    async def _get_kline(self) -> pd.DataFrame:
        result = await StockDbUtils.read(
            DbTable.DAILY_KLINE, where={"ticker": self.ticker}, output="df"
        )
        return result

    async def _get_rs(self) -> pd.DataFrame:
        result = await StockDbUtils.read(
            DbTable.RELATIVE_STRENGTH, where={"ticker": self.ticker}, output="df"
        )
        return result

    async def handle(self) -> pd.DataFrame:
        kline = await self._get_kline()
        rs = await self._get_rs()

        kline["date"] = pd.to_datetime(kline["date"]).dt.date
        kline = kline[["date", "open", "high", "low", "close", "volume"]]
        kline.set_index("date", inplace=True)

        rs["date"] = pd.to_datetime(rs["date"]).dt.date
        rs = rs[["date", "rscore"]]
        rs.set_index("date", inplace=True)

        df = kline.join(rs, how="inner")
        df.reset_index(inplace=True)
        df.sort_values(by="date", inplace=True)

        # Volume Colors
        volume_colors = [
            "green" if close > open_ else "red"
            for close, open_ in zip(df["close"], df["open"])
        ]

        fig = go.Figure()

        # Adding OHLC chart
        fig.add_trace(
            go.Ohlc(
                x=df["date"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="OHLC",
                yaxis="y",
            )
        )

        # Adding volume as bars with conditional colors
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["volume"],
                marker_color=volume_colors,
                name="Volume",
                yaxis="y3",
            )
        )
        # Rs
        fig.add_trace(
            go.Scatter(
                x=df["date"], y=df["rscore"], mode="lines", name="RS", yaxis="y2"
            )
        )

        fig.update_layout(
            title=f"{self.ticker} - RS",
            yaxis=dict(
                domain=[
                    0.35,
                    1,
                ],
                title="OHLC",
            ),
            yaxis2=dict(title="RS", overlaying="y", side="right", range=[0, 100]),
            yaxis3=dict(
                domain=[0, 0.3], title="Volume"  # Positioning volume at the bottom
            ),
            xaxis_rangeslider_visible=False,
        )

        # fig.show()
        return fig.to_html(full_html=False, include_plotlyjs="cdn")
