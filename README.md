# Keepers

**Swipe right to keep it. Swipe left to let it go.**

Keepers turns a pile of your kid's old stuff into a deck of dating profiles. They swipe through it on their phone. You get a list of what to keep and what to donate.

## Why I made this

My daughter has a lot of her stuff in boxes in my garage. Books, clothes, school projects, things from every age. Going through it together one item at a time is slow. Texting "do you still want this?" a hundred times is miserable for both of us.

So I made it a game. I lay a batch of things on the floor and take one picture. Claude cuts that picture into one card per item and writes each thing a short, goofy dating profile. She swipes through the round on her iPhone whenever she feels like it. When she's done, she texts me the list. I box up the keepers, drop the rest at the donation center, and send the next round.

No more "I'll look at it next time I'm over." A whole box becomes a two minute game.

## How it works

1. **Lay it out.** Put a batch of stuff on the floor with a little space between things. Take one photo from above.
2. **Make a round.** Claude (or the included tool) cuts the photo into a card per item and gives each one a name and a profile.
3. **Send the link.** The newest round opens on its own. Swipe right to keep, left to donate. Undo is always one tap away.
4. **Get the list.** The last screen shows everything kept and donated. Tap any item to switch it. One button copies the list and opens a text to you.
5. **Do the thing.** Keep pile, donate pile, done. Next round.

## Features

* Feels like a dating app: drag, tilt, stamp, fly away.
* Undo, plus a summary screen where any choice can be switched.
* Rounds. Each batch is its own round, and progress is saved on the phone.
* Works in the phone's browser. Nothing to install, no account.
* One HTML file. No build step, no framework, no tracking.
* Light and dark mode. Keyboard arrows work on a laptop.

## Try it

```
python3 -m http.server
```

Then open http://localhost:8000. The practice round uses made up books.

## Make your own rounds

You need Python 3 with Pillow and OpenCV:

```
pip install -r requirements.txt
```

Then, for each photo:

```
python3 tools/keepers.py detect photo.jpg              # guesses a box per item, saves boxes.json and detect.jpg
python3 tools/keepers.py grid photo.jpg                # or draw a percent grid and write the boxes yourself
python3 tools/keepers.py crop photo.jpg boxes.json --round books --title "Books from the blue tote" --where "Blue tote · garage"
```

`crop` saves one image per item in `rounds/books/`, adds the items to `rounds.json`, and makes a contact sheet (`_sheet.jpg`) so you can check every crop. Then open `rounds.json` and give each item a name, a bio and a few tags.

Or skip the typing: give Claude the photo and this repo and say "make a Keepers round from this." It reads the photo, finds the items, writes the profiles, and builds the round.

Detection works best on a plain floor with space between items. Touching items get merged into one box, so split those by hand.

## Host it

Keepers is a static site. GitHub Pages, Netlify, Cloudflare Pages or any web host works. To ship it as a single file, run:

```
python3 tools/keepers.py build
```

That bakes `rounds.json` into `dist/index.html`. Upload it with the `rounds/` folder next to it.

Put your number in `rounds.json` under `config.dadPhone` so the text button knows where to go.

## rounds.json

```json
{
  "config": {
    "appName": "Keepers",
    "kidName": "",
    "dadName": "Dad",
    "dadPhone": "+15155550123",
    "keepWord": "Keep",
    "tossWord": "Donate",
    "keepStamp": "Keeper"
  },
  "rounds": [
    {
      "id": "books",
      "title": "Books from the blue tote",
      "note": "Found these under the workbench.",
      "date": "Oct 18",
      "items": [
        {
          "id": "books-01",
          "img": "rounds/books/01.jpg",
          "name": "The Moon Owes Me Twelve Dollars",
          "sub": "Wren Abernathy · Paperback",
          "where": "Blue tote · garage",
          "bio": "We met in fifth grade. Still not mad about the twelve dollars.",
          "tags": ["Space", "Funny"]
        }
      ]
    }
  ]
}
```

The newest unfinished round opens first. Older rounds stay under **Rounds**.

## Privacy

Photos live wherever you host them. Keepers has no server, no analytics and no accounts. Swipes are saved only on your kid's phone until they send you the list.

## Writing good profiles

The bios are what make it fun. A few rules that work:

* Write as the item, in first person. "I was there for every late night."
* Name a real memory if you know one. It helps them decide.
* Keep it kind. The point is to make letting go easy, not to guilt anyone into keeping things.
* Two or three short sentences. Three tags.

## Credits

Made by Jason O'Connell ([hurtz](https://github.com/hurtz), hurtz2k on Reddit) with Claude.

## License

MIT. Use it, change it, share it. See [LICENSE](LICENSE).

Want it without any setup? A hosted version, where you upload a photo and get a finished round back, is in the works.
