# 機能
panty-loveの画像と動画ファイルをダウンロードします。
# 環境
Windows10 1909 または Ubuntu 18.04 LTS  
python 3.6.9  
Google Chrome 81.0.4044.113  
WebDriver 81.0.4044.113  
※多少古いバージョンでも動くはず
# インストール
1. 作業用ディレクトリを作成  
2. crawler.pyとconfig.iniを配置  
必要に応じて実行権限を付与。  
3. config.iniをカスタマイズ  
LOGIN_URL ： ログインページのURL  
USER_ID ： ログイン名  
PASSWORD ： パスワード  
BLACK_LIST ： 画像枚数チェック除外リスト    
BROWSER_WAIT ： Google Chromeからの応答待機時間(秒)
# 実行  
crawler.pyを実行
# 補足
* 対応サイト  
panty-loveとpanty-love2に対応しています。  
* ダウンロード先  
作業用ディレクトリ直下に個人別にディレクトリを作成し画像と動画を配置します。  
* BLACK_LISTについて  
サムネイル画像と実際の画像ファイルとのリンクが切れている問題が存在します。このためマイページに表示される画像の枚数とダウンロードしたファイル数が一致しないケースがあります。BLACK_LISTにディレクトリ名をリスト形式で登録することにより、ダウンロード済み判定をスキップする仕様としました。  
config.ini内のBLACK_LISTにディレクトリ名を列挙します。JSON形式のため文字列をダブルクォーテーションで括る点に注意してください。  
例：BLACK_LIST = ["aaa","bbb"]  
* 例外処理  
完全ではありません。  
ダウンロード済みのファイルをスキップする機能を実装していますので再実行を繰り返してください。  
* ダウンロードサイズ  
panty-love ： 約300GB  
panty-love2 ： 約210GB  
