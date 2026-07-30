export type Resolution = "5" | "30" | "D" | "1D";

type ApiTimeframe = "5m" | "30m" | "1d";

export interface SymbolInfo {
  ticker: string;
  name: string;
  full_name: string;
  exchange: "SSE" | "SZSE";
  listed_exchange: "SSE" | "SZSE";
  timezone: "Asia/Shanghai";
  session: "0930-1130,1300-1500";
  type: "stock";
  supported_resolutions: ["5", "30", "D"];
  has_intraday: true;
  has_daily: true;
  has_weekly_and_monthly: false;
  minmov: 1;
  pricescale: 100000000;
}

export interface HistoryBar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketDatafeed {
  onReady(callback: (configuration: { supported_resolutions: ["5", "30", "D"] }) => void): void;
  resolveSymbol(
    symbol: string,
    onResolve: (symbolInfo: SymbolInfo) => void,
    onError: (reason: string) => void,
  ): void;
  getBars(
    symbolInfo: Pick<SymbolInfo, "ticker">,
    resolution: string,
    periodParams: { from: number; to: number; countBack?: number },
    onHistory: (bars: HistoryBar[], metadata: { noData: boolean }) => void,
    onError: (reason: string) => void,
  ): Promise<void>;
}

type Fetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

interface ApiBar {
  symbol: string;
  timeframe: ApiTimeframe;
  adjustment: "NONE" | "QFQ" | "HFQ";
  open_time: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
}

interface ApiPage {
  bars: ApiBar[];
}

const SYMBOL = /^(SSE|SZSE):\d{6}$/;

function apiTimeframe(resolution: string): ApiTimeframe | undefined {
  if (resolution === "5") return "5m";
  if (resolution === "30") return "30m";
  if (resolution === "D" || resolution === "1D") return "1d";
  return undefined;
}

function asFiniteNumber(value: unknown): number | undefined {
  if (typeof value !== "string" || value.trim() === "") return undefined;
  const number = Number(value);
  return Number.isFinite(number) ? number : undefined;
}

function asEpochSeconds(value: unknown): number | undefined {
  if (typeof value !== "string" || !value.endsWith("Z")) return undefined;
  const milliseconds = Date.parse(value);
  return Number.isFinite(milliseconds) ? milliseconds / 1000 : undefined;
}

function isApiPage(value: unknown): value is ApiPage {
  return typeof value === "object" && value !== null && Array.isArray((value as { bars?: unknown }).bars);
}

function mapBar(bar: ApiBar, symbol: string, timeframe: ApiTimeframe): HistoryBar | undefined {
  if (bar.symbol !== symbol || bar.timeframe !== timeframe || bar.adjustment !== "NONE") return undefined;
  const time = asEpochSeconds(bar.open_time);
  const open = asFiniteNumber(bar.open);
  const high = asFiniteNumber(bar.high);
  const low = asFiniteNumber(bar.low);
  const close = asFiniteNumber(bar.close);
  const volume = asFiniteNumber(bar.volume);
  if (
    time === undefined || open === undefined || high === undefined || low === undefined ||
    close === undefined || volume === undefined
  ) return undefined;
  return { time, open, high, low, close, volume };
}

function symbolInfo(symbol: string): SymbolInfo {
  const exchange = symbol.slice(0, symbol.indexOf(":")) as "SSE" | "SZSE";
  return {
    ticker: symbol,
    name: symbol,
    full_name: symbol,
    exchange,
    listed_exchange: exchange,
    timezone: "Asia/Shanghai",
    session: "0930-1130,1300-1500",
    type: "stock",
    supported_resolutions: ["5", "30", "D"],
    has_intraday: true,
    has_daily: true,
    has_weekly_and_monthly: false,
    minmov: 1,
    pricescale: 100000000,
  };
}

export function createMarketDatafeed(fetchImpl: Fetch = fetch): MarketDatafeed {
  return {
    onReady(callback) {
      callback({ supported_resolutions: ["5", "30", "D"] });
    },

    resolveSymbol(symbol, onResolve, onError) {
      if (!SYMBOL.test(symbol)) {
        onError("INVALID_SYMBOL");
        return;
      }
      onResolve(symbolInfo(symbol));
    },

    async getBars(symbol, resolution, period, onHistory, onError) {
      const timeframe = apiTimeframe(resolution);
      if (!timeframe) {
        onError("UNSUPPORTED_RESOLUTION");
        return;
      }
      if (!SYMBOL.test(symbol.ticker)) {
        onError("INVALID_SYMBOL");
        return;
      }
      const limit = period.countBack ?? 5000;
      if (!Number.isInteger(limit) || limit < 1 || limit > 5000) {
        onError("LIMIT_EXCEEDED");
        return;
      }

      const parameters = new URLSearchParams({
        symbol: symbol.ticker,
        timeframe,
        adjustment: "NONE",
        start: new Date(period.from * 1000).toISOString(),
        end: new Date(period.to * 1000).toISOString(),
        limit: String(limit),
      });
      let response: Response;
      try {
        response = await fetchImpl(`/api/market/bars?${parameters.toString()}`);
      } catch {
        onError("PROVIDER_UNAVAILABLE");
        return;
      }

      const payload: unknown = await response.json().catch(() => undefined);
      if (!response.ok) {
        const code = (payload as { error?: { code?: unknown } } | undefined)?.error?.code;
        onError(typeof code === "string" ? code : "INVALID_BAR_PAGE");
        return;
      }
      if (!isApiPage(payload)) {
        onError("INVALID_BAR_PAGE");
        return;
      }

      const bars = payload.bars.map((bar) => mapBar(bar, symbol.ticker, timeframe));
      if (bars.some((bar) => bar === undefined)) {
        onError("INVALID_BAR_PAGE");
        return;
      }
      const mapped = bars as HistoryBar[];
      if (mapped.some((bar, index) => index > 0 && mapped[index - 1].time >= bar.time)) {
        onError("INVALID_BAR_PAGE");
        return;
      }
      onHistory(mapped, { noData: mapped.length === 0 });
    },
  };
}
