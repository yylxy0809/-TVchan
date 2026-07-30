import type { MarketDatafeed } from "./datafeed/market-datafeed";

export interface WidgetFactory {
  (options: { datafeed: MarketDatafeed }): void;
}

export function mountTradingViewWidget(createWidget: WidgetFactory, datafeed: MarketDatafeed): void {
  createWidget({ datafeed });
}
