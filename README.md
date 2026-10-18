# Sift

**Swipe right to keep it. Swipe left to let it go.**

**[Open the Sift app](https://claude.ai/artifact/HJ9XSeBYKeMdY8UpvhPMWW)** (runs on Claude; this repo is the source code)

Sift turns a pile of your kid's old stuff into a deck of dating profiles. They swipe through it on their phone. You get a list of what to keep and what to donate.

## Why I made this

My daughter has a lot of her stuff in boxes in my garage. Books, clothes, school projects, things from every age. Going through it together one item at a time is slow. Texting "do you still want this?" a hundred times is miserable for both of us.

So I made it a game. I lay a batch of things on the floor and take one picture with my phone. Claude finds every item in the photo, cuts each one out, and writes it a short, goofy dating profile. I fix anything it got wrong and hit send. She swipes through the round on her iPhone whenever she feels like it, and her picks show up on my side as she goes. I box up the keepers, drop the rest at the donation center, and send the next round.

No more "I'll look at i## How it works

There are two sides: **Dad's studio** and **her swipe deck**. Same page, same link.

**Studio (you)**
1. **Snap the stuff.** Lay a batch out with a little space between things and take one photo from above. Or switch to "one thing per photo" and snap items one by one.
2. **Check the boxes.** Claude draws a box around every item it finds, then each box snaps tight to the item. Drag to move, drag a corner to resize, tap × to drop one, or draw one it missed.
3. **Name everything.** Each item is cut out and Claude names it (reading book titles off covers), adds details, tags and a dating profile. Edit anything. Rotate a crop. Ask Claude again on one item.
4. **Preview and send.** See exactly what she'll see, then send. Copy a ready text with the link for her.

**Swipe deck (her)**
5. **Swipe.** Right to keep, left to donate. Undo is one tap. Tap a card to read the full profile.
6. **Fix it at the end.** The summary shows both piles. Tap anything to switch it.

**Back to you**
7. **Watch it land.** Her picks show up in the studio live: who's waiting, how far she got, and the final keep and donate lists. Tick items off as you pack or drop them off. Archive the round when it's done.

Everything saves as you go, so a half finished round is still there if your phone locks.

## Features

* Looks and feels like a native iPhone app, in the browser. System font, iOS colors, light and dark mode.
* Feels like a dating app: drag, tilt, stamp, fly away.
* AI item finding with a hand editor for anything it misses.
* AI names and profiles, every field editable.
* Live two way sync: send rounds, get picks back, no copy and paste.
* Packing checklist for the keep pile and donate pile.
* Preview her side before you send. Preview swipes are never saved.
* Big touch targets. Keyboard arrows on a laptop.
* One HTML file. No framework, no tracking.

## Where it runs

Sift runs as a Claude artifact, which gives the page three things it can't do on its own: a shared database (rounds and picks), image storage, and Claude's eyes (finding and naming items in photos).

To let her swipes sync back, share the page with her by email and set her to **Editor**, with the public link off. If she opens it some other way, the deck still works and the summary offers a "text Dad the list" button instead.

The page also runs as a plain static site with no Claude features. It then shows rounds baked into `rounds.json`, which you can build with the photo tool below.

ing.
* Light and dark mode. Keyboard arrows work on a laptop.

## Try it

```
python3 -m http.server
```

Then open http://localhost:8000. The practice round uses made up books.

## Make rounds without Claude (static version)

You need Python 3 with Pillow and OpenCV:

```
pip install -r requirements.txt
```

Then, for each photo:

```
python3 tools/sift.py detect photo.jpg              # guesses a box per item, saves boxes.json and detect.jpg
python3 tools/sift.py grid photo.jpg                # or draw a percent grid and write the boxes yourself
python3 tools/sift.py crop photo.jpg boxes.json --round books --title "Books from the blue tote" --where "Blue tote · garage"
```

`crop` saves one image per item in `rounds/books/`, adds the items to `rounds.json`, and makes a contact sheet (`_sheet.jpg`) so you can check every crop. Then open `rounds.json` and give each item a name, a bio and a few tags.

Or skip the typing: give Claude the photo and this repo and say "make a Sift round from this." It reads the photo, finds the items, writes the profiles, and builds the round.

Detection works best on a plain floor with space between items. Touching items get merged into one box, so split those by hand.

## Host it

Sift is a static site. GitHub Pages, Netlify, Cloudflare Pages or any web host works. To ship it as a single file, run:

```
python3 tools/sift.py build
```

That bakes `rounds.json` into `dist/index.html`. Upload it with the `rounds/` folder next to it.

Put your number in `rounds.json` under `config.dadPhone` so the text button knows where to go.

## rounds.json

```json
{
  "config": {
    "appName": "Sift",
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

Photos live wherever you host them. Sift has no server, no analytics and no accounts. Swipes are saved only on your kid's phone until they send you the list.

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

Want it without any setup? A hosted version for families is in the works.
