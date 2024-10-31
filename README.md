# 🗳️ Presidentigami.com

### The Official (and only) Electoral College Scorigami Tracker for the 2024 Presidential Election! 

## 👋 Introduction

Gm, I'm excited to share a quick weekend project of mine and claim the $50 my webdev buddy now owes me. 

While all may remember the winner of the 2020 election, fewer may recall the actual electoral college score, and far, far, fewer are likely aware of the fact that this score - 306 v 232 - was the identical outcome of the 2016 electoral college.

While some call this fact fun US politics trivia, many seasoned NFL fans have their own word for this result 'non-Scorigami'

## 🏈 What is Scorigami?

Scorigami refers to a unique final score in an NFL game that has never happened before in the league's history. The idea was popularized by Jon Bois, who created a project to track and predict new, never-before-seen NFL scores NFLScorigami.com. Every time a game ends with a final score that has never occurred before in NFL history, it would be considered a "Scorigami." In said events, myself and countless others- also recording double digits steps on their Apple Watches during Fall Sundays- rejoice in the glory that is the gift of a Scorigami.

In anticipation of the 2020 election, I tweeted, pledging my endorsement, not for a candidate, but for an outcome - an electoral college Scorigami. With 538 different possible scores for the Electoral College and only 13 of these being occupied as a historical result, I ignorantly assumed to have placed my hopes in the safest basket.

Unfortunately, after the dust settled, I was left in shock at the realization that for the first time in US Election History-  an Electoral College score was repeated. It was by far the most significant event surrounding the 2020 election results….

## 🚀 The Project

As the 2024 election arrives, in order to hedge against my disappointment and set realistic expectations, I have created Presidentigami.com

Similar to how NFLScorigami.com tracks the probability of a Scorigami for NFL games, based on current and projected scores, Presidentigami tracks the likelihood of an Electoral College Scorigami leveraging the current market betting odds in each district to infer the probability of Scorigami based on the 72 quadrillion (that's a real number) possible Electoral College outcomes- more intuitively 2^56.

## 🔧 Technical Details

### Methodology
While NFL Scorigami is able to track the probability of a Scorigami, academically P(S), via the current score of the game, doing so for the US election proves to be a bit more difficult prior to actual election night. Because of this, we elected to instead leverage the current betting markets to back into an estimated probability for each electoral college outcome to then find P(S) in aggregate.

Mentioned betting odds per district are as follows, whereas a $1 resolving bet:
- On California to be won by a Democrat costs $0.988 - inferred 98.8% chance Democrat
- On Texas to be won by a Democrat costs $0.10 - inferred 10% chance Democrat

Therein, it can be assumed that the probability we see California Blue and Texas Red is (0.988 * (1-0.1)) or, ~89%. 

### Data Source
Current odds are fetched every 15 minutes from Polymarket.com, a Web3 based betting platform that uses smart contracts for what they call 'markets'. Because of the decentralized nature of Web3/Polymarket, it makes retrieval of these odds extremely accessible whereas legacy bookmakers tend to be more restrictive.**

Scaling the above across all 56 electoral districts*, we can continue this practice to get an assumed probability of all 2^56 possible outcomes. Finally, said outcomes can then be joined to historic electoral college outcomes to find our resulting probability of Scorigami.

The skeptical reader may now be wondering what resources I have access to that allow me to perform such a compute heavy calculation every 15 minutes. The answer is, I am cheating. In our process, any district with an assumed probability greater than 90% for a given party is essentially hardcoded to that outcome and will never change state. This makes our process much more manageable and I sleep well knowing I'm not burning electricity acting like Nebraska 3rd will ever go Blue.
For background, following Pieter Levels (Levels.io) appearance on the Lex Friedmann podcast detailing the several projects he has built ground-up running on a single VPS, I thought it would be fun to take a stab at doing the same despite having l̶i̶t̶t̶l̶e̶ no experience.


## 🛠️ Fun Utility Notes

### Map Generation
Instead of having to build my own version of an interactive electoral college map to generate images of possible outcomes, I set up a Selenium script that uses a dictionary with each states outcome to interact with race to 270's chart, take a screenshot then hash the file name based on the outcome. The 100 most likely outcomes were done locally and transferred over, though in the route that serves these images, in the event one hasn't been produced, the function is able to go retrieve it at run time.

### Faithless Electors
'Faithless Electors' are instances where an elector will (normally symbolically) cast a vote against the wishes of the popular vote of their district to a candidate who does not have a real chance at winning. Ie. In 2016 Clinton won Washington, though an elector cast a vote for 'Faith Spotted Eagle' Presidentigami does not recognize the legitimacy of Faithless Electors and only leverages popular vote based outcomes for each district (read, not what their electors did) when determining historical scores. Since race to 270 does not have a clean way to extract (scrape) this information without some form of NLP, we opted to just pass instances of this to an OpenAI API to reconfigure the outcome dictionary to be aligned to how The People decided

## 💻 Hardware Specs

### Local Development
- i7 14700k
- NVIDIA 4070 Super
- 128gb RAM 6000MHz
- 2tb disk

### Deployment
- Digital Ocean VPS (Ubuntu)
- 2 (Shared) vcpu
- 4gb RAM
- 120gb disk

*The above doesn't really matter, but I want to give everyone the chance to laugh at me, knowing I developed my entire build locally and then thought I would just be able to ship the same codebase to a $30/month VPS and expect it to run like my local*

## 📝 Notes

\* There are 56 electoral districts because of the Nebraska, Maine splits, and DC, for some reason, gets some as well

\** It is well understood that Web3/cryptocurrency tech disproportionally appeals to those favoring 'Right Wing' ideals. One may be quick to claim that the platform odds will reflect this favoritism; in defense of this and in observance of Polymarkets 1.7 billion dollars in current volume for the election, I urge you to consult the efficient-market-hypothesis.

\*** Presidentigami and its creator do not endorse any individual candidate or party
