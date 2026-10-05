"""Strategy topics the generator rotates through.

Each topic has:
  title  - the article headline it aims for
  query  - the web search phrase used to gather research material
  angle  - extra steering for the model

The generator publishes one topic per run and remembers which ones are already
done (articles/state.json), so no topic is repeated until the list runs out.
Add new topics at the bottom - they are used in order.

The search phrase is only used to find *source material*. The model must always
write an original article and never copy source sentences.
"""

TOPICS = [
    {
        "title": "How to Defend Your Big Blind in Microstakes",
        "query": "how to defend big blind microstakes strategy",
        "angle": "explain the price offered, defend frequencies and why microstakes opponents under- and over-bluff",
    },
    {
        "title": "3-Betting Explained: When, Why and How Much",
        "query": "3-betting strategy when to 3bet sizing poker",
        "angle": "value vs bluff 3-bets, sizing, and how to react to a 3-bet",
    },
    {
        "title": "C-Bet Sizing and Board Texture",
        "query": "continuation bet sizing board texture strategy",
        "angle": "small vs large c-bets, dry vs wet boards, and when to give up",
    },
    {
        "title": "Thin Value Betting on the River",
        "query": "thin value betting river poker strategy",
        "angle": "how to spot thin value, sizing, and the risk of value-owning yourself",
    },
    {
        "title": "Playing From the Small Blind",
        "query": "small blind play strategy poker preflop",
        "angle": "the worst seat, limp vs raise, and why the small blind loses money",
    },
    {
        "title": "Bluff-Catching at the Right Frequency",
        "query": "bluff catching frequency poker strategy",
        "angle": "minimum defence frequency, blockers and villain tendencies",
    },
    {
        "title": "Pot Odds, Equity and Implied Odds",
        "query": "pot odds implied odds equity poker explained",
        "angle": "worked examples and how implied odds change a close call",
    },
    {
        "title": "Check-Raising the Flop",
        "query": "flop check raise strategy poker",
        "angle": "value vs semi-bluff check-raises and why position matters",
    },
    {
        "title": "Barreling the Turn and River",
        "query": "turn river barrel bluffing poker strategy",
        "angle": "when to keep firing, which turns to barrel, and giving up",
    },
    {
        "title": "Preflop Ranges: Opening by Position",
        "query": "preflop opening ranges by position poker",
        "angle": "why ranges widen from early to late position and the rake impact",
    },
    {
        "title": "4-Betting and Facing 3-Bets",
        "query": "4-betting strategy facing 3bet poker",
        "angle": "value vs light 4-bets, sizing and stack-depth effects",
    },
    {
        "title": "Playing Draws: Semi-Bluff or Call",
        "query": "playing draws semi bluff vs call poker strategy",
        "angle": "fold equity, equity, and when raising a draw is best",
    },
    {
        "title": "Exploiting Calling Stations",
        "query": "how to exploit calling stations poker strategy",
        "angle": "value-heavy lines, thin value and cutting bluffs",
    },
    {
        "title": "Beating Nits and Tight Players",
        "query": "how to exploit tight players nits poker strategy",
        "angle": "stealing more, respecting their aggression and folding marginal hands",
    },
    {
        "title": "Multiway Pots: Adjusting Your Strategy",
        "query": "multiway pot strategy poker adjustments",
        "angle": "tighter c-bets, less bluffing and stronger value thresholds",
    },
    {
        "title": "Bankroll Management for Microstakes",
        "query": "bankroll management microstakes poker rules",
        "angle": "buy-in rules, moving up and down, and variance",
    },
    {
        "title": "Table and Seat Selection",
        "query": "table selection seat selection poker strategy",
        "angle": "finding good games and staying to the left of the fish",
    },
    {
        "title": "Hand Reading and Range Narrowing",
        "query": "hand reading range narrowing poker strategy",
        "angle": "turning a bet sequence into a range of hands",
    },
    {
        "title": "Bet Sizing: Choosing the Right Amount",
        "query": "bet sizing strategy poker value bluff",
        "angle": "how sizing encodes strength and how to exploit sizing tells",
    },
    {
        "title": "Set Mining With Small Pocket Pairs",
        "query": "set mining small pocket pairs odds implied odds",
        "angle": "the 15-to-1 rule, position and stack depth",
    },
    {
        "title": "C-Betting In Position vs Out of Position",
        "query": "c-betting in position vs out of position poker",
        "angle": "why position changes everything about the flop",
    },
    {
        "title": "Limping vs Raising Preflop",
        "query": "limping vs raising preflop microstakes strategy",
        "angle": "isolation raises, limped pots and the rake argument",
    },
    {
        "title": "Dealing With Aggressive Maniacs",
        "query": "playing against maniacs aggressive opponents poker",
        "angle": "widening value, trapping and avoiding tilt",
    },
    {
        "title": "Overbets Explained",
        "query": "overbet strategy poker when to overbet",
        "angle": "polarised ranges, blockers and scary runouts",
    },
    {
        "title": "GTO vs Exploitative Play: When to Deviate",
        "query": "gto vs exploitative play when to deviate poker",
        "angle": "defaulting to solid play and deviating to attack leaks",
    },
    {
        "title": "Balancing Value Bets and Bluffs",
        "query": "value to bluff ratio balanced range poker",
        "angle": "why balance matters less at microstakes and when it still does",
    },
]
