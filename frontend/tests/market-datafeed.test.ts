import { describe, expect, it, vi } from "vitest";

import { createMarketDatafeed, type HistoryBar } from "../src/tradingview/datafeed/market-datafeed";
import { mountTradingViewWidget } from "../src/tradingview/widget";

const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

const validPage = {
  bars: [{
    symbol: "SSE:600000",
    timeframe: "1d",
    adjustment: "NONE",
    open_time: "2026-01-02T01:30:00Z",
    open: "10.0",
    high: "12.0",
    low: "9.0",
    close: "11.0",
    volume: "1000",
  }],
};

describe("market datafeed", () => {
  it("resolves only canonical symbols without fetching", () => {
    const fetcher = vi.fn();
    const feed = createMarketDatafeed(fetcher);
    const onResolve = vi.fn();
    const onError = vi.fn();

    feed.resolveSymbol("SSE:600000", onResolve, onError);
    feed.resolveSymbol("sh.600000", onResolve, onError);

    expect(onResolve).toHaveBeenCalledWith(expect.objectContaining({ timezone: "Asia/Shanghai", pricescale: 100000000 }));
    expect(onError).toHaveBeenCalledWith("INVALID_SYMBOL");
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("exposes the static datafeed surface and binds only that datafeed to the widget", () => {
    const feed = createMarketDatafeed(vi.fn());
    const onReady = vi.fn();
    const createWidget = vi.fn();

    feed.onReady(onReady);
    mountTradingViewWidget(createWidget, feed);

    expect(onReady).toHaveBeenCalledWith({ supported_resolutions: ["5", "30", "D"] });
    expect(createWidget).toHaveBeenCalledWith({ datafeed: feed });
    expect("subscribeBars" in feed).toBe(false);
    expect("unsubscribeBars" in feed).toBe(false);
    expect("getServerTime" in feed).toBe(false);
  });

  it("maps TradingView bars to the relative market endpoint", async () => {
    const fetcher = vi.fn().mockResolvedValue(response(validPage));
    const feed = createMarketDatafeed(fetcher);
    const onHistory = vi.fn();
    const onError = vi.fn();

    await feed.getBars({ ticker: "SSE:600000" }, "D", { from: 1767317400, to: 1767749400, countBack: 1 }, onHistory, onError);

    expect(fetcher).toHaveBeenCalledOnce();
    expect(fetcher.mock.calls[0][0]).toContain("/api/market/bars?");
    expect(fetcher.mock.calls[0][0]).toContain("timeframe=1d");
    expect(fetcher.mock.calls[0][0]).toContain("limit=1");
    expect(onHistory).toHaveBeenCalledWith(expect.any(Array), { noData: false });
    expect(onError).not.toHaveBeenCalled();
  });

  it("rejects unsupported resolutions and excessive limits without I/O", async () => {
    const fetcher = vi.fn();
    const feed = createMarketDatafeed(fetcher);
    const onHistory = vi.fn();
    const onError = vi.fn();

    await feed.getBars({ ticker: "SSE:600000" }, "60", { from: 1, to: 2 }, onHistory, onError);
    await feed.getBars({ ticker: "SSE:600000" }, "D", { from: 1, to: 2, countBack: 5001 }, onHistory, onError);

    expect(onError).toHaveBeenNthCalledWith(1, "UNSUPPORTED_RESOLUTION");
    expect(onError).toHaveBeenNthCalledWith(2, "LIMIT_EXCEEDED");
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("handles no-data and typed failures without nextTime", async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(response({ bars: [] }))
      .mockResolvedValueOnce(response({ error: { code: "PROVIDER_TIMEOUT" } }, 504));
    const feed = createMarketDatafeed(fetcher);
    const onHistory = vi.fn<(bars: HistoryBar[], metadata: { noData: boolean }) => void>();
    const onError = vi.fn();

    await feed.getBars({ ticker: "SSE:600000" }, "D", { from: 1, to: 2 }, onHistory, onError);
    await feed.getBars({ ticker: "SSE:600000" }, "D", { from: 1, to: 2 }, onHistory, onError);

    expect(onHistory).toHaveBeenCalledWith([], { noData: true });
    expect(onError).toHaveBeenCalledWith("PROVIDER_TIMEOUT");
  });

  it("rejects malformed API bars", async () => {
    const fetcher = vi.fn().mockResolvedValue(response({ bars: [{ ...validPage.bars[0], close: "not-a-number" }] }));
    const feed = createMarketDatafeed(fetcher);
    const onError = vi.fn();

    await feed.getBars({ ticker: "SSE:600000" }, "D", { from: 1, to: 2 }, vi.fn(), onError);

    expect(onError).toHaveBeenCalledWith("INVALID_BAR_PAGE");
  });
});
