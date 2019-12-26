import click

# I DONT GET CLICK
@click.group()
def main():
    pass

@main.command()

@click.option('--scrape_game_list','-sgl', default="s8",
              help='Scrapes urls for games, which have been played in season',
              type=click.Choice(["s5", "s6", "s7", "s8", "s9"]),
              multiple=False, show_default=True)
def get_matches(season):
    print("Scraping season")
    # from scrape.lol_old.LOL_scraper import scrape_season
    # scrape_season()


@main.command()
@click.pass_context
@click.option('--scrape_stats','ss',
              help='Scrapes statistics for pending games')
def scrape_stats():
    print("scraping games")

    # from scrape.lol_old.LOL_scrape_games import scrape_pending_games
    # scrape_pending_games()


@main.command()
@click.option('--scrape_all','sa', default="s8",
              help='Performs both other actions in sequence',
              type=click.Choice(["s5", "s6", "s7", "s8"]),
              multiple=False, show_default=True)
def scrape_lol(season):
    print("dong both")
    # from scrape.lol_old.LOL_scraper import scrape_season
    # scrape_season()
    # from scrape.lol_old.LOL_scrape_games import scrape_pending_games
    # scrape_pending_games()
    pass


if __name__ == "__main__":
    main()
