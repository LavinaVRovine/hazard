# Esport winner predictor
> **Still Work in progress!**

> Practice project made for learning purposes



Project is made of three part. <br> 
First part scrapes past statistic for LoL, Dota and CSGO. <br>
Second part predicts winner of a match based on scraped statistics.<br>
Third hits selected CZ bookies, and if a games are played, compares the odds of 
predictor against bookie odds and suggest appropriate action. Does not bet itself.


![](header.png)

## Reality check
Currently LoL and CS:GO seems to be working reasonably well.

Accuracy score (.score, one of the metrics used) for games:
<ul>
<li>LoL ~73% (RandomForrest)</li>
<li>Dota ~68% (RandomForrest)</li>
<li>CS:GO ~70% (GradientBoosting)</li>
</ul>

Dota does not deliver in real scenario.

## Usage example

Run main.py --help for possible actions.

OR

run X_main.py in scrape folder of the game to download the statistics (
which might take a while...), then run main

main.py --compare_odds _name_of_game_ :
Checks if any games are being offered at 
implemented bookies and if so, compares predicted odds against bookie odds,
and then sends email with recommended action.

## Development setup

Just install dependencies from environment.yaml .

## Release History

 * Project is not intended for production

## Meta

[Pavel Klammert](http://www.klammert.cz) – [@LavinaVRovine](https://twitter.com/lavinavrovine) – pavelklammert@gmail.com

[https://github.com/LavinaVRovine](https://github.com/LavinaVRovine/)

Distributed under the MIT license. See ``LICENSE`` for more information.



## Contributing

1. Fork it (<https://github.com/yourname/yourproject/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

<!-- Markdown link & img dfn's -->
[npm-image]: https://img.shields.io/npm/v/datadog-metrics.svg?style=flat-square
[npm-url]: https://npmjs.org/package/datadog-metrics
[npm-downloads]: https://img.shields.io/npm/dm/datadog-metrics.svg?style=flat-square
[travis-image]: https://img.shields.io/travis/dbader/node-datadog-metrics/master.svg?style=flat-square
[travis-url]: https://travis-ci.org/dbader/node-datadog-metrics
[wiki]: https://github.com/yourname/yourproject/wiki
