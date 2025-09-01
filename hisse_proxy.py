import sys
import json
import urllib.request
import urllib.error

YAHOO_API_URL_TEMPLATE = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}.IS?range=1y&interval=1d"

def get_stock_data(ticker):
    """Fetches stock data from Yahoo Finance for a given ticker and prints it to stdout."""
    
    yahoo_url = YAHOO_API_URL_TEMPLATE.format(ticker=ticker.upper())
    
    # Log to stderr so it doesn't interfere with the JSON output
    print(f"Talep gönderiliyor: {yahoo_url}", file=sys.stderr)

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        req = urllib.request.Request(yahoo_url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            response_body = response.read()
            
            # Check if the response is valid JSON before printing
            try:
                json.loads(response_body)
                # Print the raw JSON data to standard output
                print(response_body.decode('utf-8'))
                return 0  # Success
            except json.JSONDecodeError:
                print("Hata: Yahoo Finance'ten gelen yanıt geçerli bir JSON değil.", file=sys.stderr)
                return 1  # Failure

    except urllib.error.HTTPError as e:
        print(f"HTTP Hatası: {e.code} {e.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"URL Hatası: {e.reason}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Kullanım: python hisse_proxy.py <HISSE_KODU>", file=sys.stderr)
        print("Örnek: python hisse_proxy.py TCELL", file=sys.stderr)
        sys.exit(1)
    
    ticker_symbol = sys.argv[1]
    exit_code = get_stock_data(ticker_symbol)
    sys.exit(exit_code)
