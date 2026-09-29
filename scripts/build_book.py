#!/usr/bin/env python3
"""Build The Quiet Between Thoughts: 30-day manuscript -> book.html -> PDF.

    python3 scripts/build_book.py          # writes output/book/book.html

Content lives here as data so the audiobook script can reuse the exact text.
Voice rules: writing-style skill (no em dashes, contractions, varied rhythm),
truth rule (rituals framed honestly, zero medical claims), Kaion's voice.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "output", "book")

W = [
    ("Week One", "The Morning", "ink_teacup.png"),
    ("Week Two", "The Body", "ink_mountain.png"),
    ("Week Three", "The Noise", "ink_flags.png"),
    ("Week Four", "The Stillness", "ink_candle.png"),
]

# (week, title, epigraph, [teaching paras], (practice label, [steps]), journal)
DAYS = [
 (0, "Before the World Enters",
  "The first minutes of the morning belong to whoever takes them.",
  ["Most people lose the day in its first two minutes. The alarm rings, the hand reaches for the phone, and before their feet touch the floor they have invited a thousand strangers into the bedroom. The news, the messages, the noise. Then they wonder why the day feels heavy before it has begun.",
   "The first minutes after waking are the most receptive of your whole day. Your mind has not yet taken anything from anyone. Whatever you place there first sets the tone for everything after. Today, you choose what enters first."],
  ("Today's practice, four minutes",
   ["Tonight, leave your phone outside the bedroom. A cheap alarm clock does its one job well.",
    "On waking, sit up slowly and say these four things, quietly or in your mind.",
    "Gratitude: thank you for this new morning, for the breath in my lungs, and the light that woke me.",
    "Strength: today I will meet whatever comes with steady energy.",
    "Guidance: may my steps be intentional, may my words be calm.",
    "Letting go: I release what I cannot control. Pause. Breathe. Now begin."]),
  "What entered your mind first this morning, and did you choose it?"),

 (0, "The Glass of Water",
  "Water answers the one who touches it.",
  ["Tonight you will do something my teacher asked of me on my first evening in the monastery. I thought it was beneath me. I was wrong about that, and about most things that year.",
   "Before you sleep, fill a glass with clean water and hold it with both hands. Say quietly: while I rest, release what is heavy. Place it beside your bed. In the morning, look at it before you look at anything else. Then pour it away.",
   "Does the water carry your worries out of the room? I will not tell you what to believe. I will tell you what you can verify: the ritual ends your day with a deliberate act instead of a scroll, it gives your last waking thought a shape, and it puts something between you and the phone in the morning. A ritual is a handle on the mind. The hand that reaches for a glass is not reaching for a screen."],
  ("Today's practice, three minutes",
   ["Before bed, fill a glass of water. Hold it with both hands for three slow breaths.",
    "Say, in a low voice: while I rest, release what is heavy. Set it beside the bed.",
    "In the morning, observe it in silence for a moment. Pour it away. Wash the glass."]),
  "What did you notice in the moment before you poured it away?"),

 (0, "Speak As If the Body Listens",
  "Your body does not understand humour. It understands repetition.",
  ["Today, no new ritual. Today you only watch your mouth.",
   "Every word you say about yourself is received as an instruction. Say “I'm stupid, I'm weak, I always fail,” even laughing while you say it, and the body does not laugh. It prepares. The shoulders tighten, the breath turns shallow, the mind stands guard. Many people are not cursed by life. They are cursed by the way they speak to themselves.",
   "You do not need to shout affirmations at a mirror. Just stop wounding yourself with your own mouth. Speak to yourself the way you would speak to a tired friend. Change the way you speak, and slowly your life begins to listen."],
  ("Today's practice, all day, zero minutes",
   ["Each time you catch a harsh word about yourself, out loud or silent, do not scold yourself for it. That is the same knife.",
    "Restate it the way a kind friend would. “I always fail” becomes “that one did not work.”",
    "Keep count on your fingers. Tonight's number is your starting point, not your verdict."]),
  "How many times did you catch the old voice today?"),

 (0, "The First Breath You Notice",
  "You have taken twenty thousand breaths today. How many did you meet?",
  ["Breathing is the only door that is always open. You cannot slow your thoughts by ordering them to slow. You can slow your breath, and the thoughts follow it down like birds settling after a clap.",
   "There is nothing mystical in this part. A long exhale tells the body the danger has passed. Every tradition found this door because every tradition had humans, and humans have always needed a way back."],
  ("Today's practice, five minutes",
   ["Sit anywhere. Back straight but not stiff, hands resting where they fall.",
    "Breathe in through the nose for a count of four.",
    "Breathe out slowly for a count of six. The exhale is the teacher; keep it longer than the inhale.",
    "Do this for five minutes. When the mind wanders, and it will, return to the counting without commentary."]),
  "Where did your mind go first, and how did you bring it back?"),

 (0, "Seal Your Day",
  "What you protect in silence works with more strength.",
  ["Before you speak to anyone tomorrow morning, seal your day. Do it before the world enters you.",
   "Place your hand over the centre of your chest. Feel the warmth of your own palm. Say silently: I protect my day. I protect my path. What is mine belongs to me. Stay there one quiet moment before you stand.",
   "The gesture takes ten seconds. Its work is simple and real: you cannot place a hand on your chest and say those words while scrolling, arguing, or hurrying. For ten seconds you are only in one place. Most people do not visit that place all day."],
  ("Today's practice, ten seconds",
   ["On waking, before speaking, place one hand flat over the centre of your chest.",
    "Say silently: I protect my day. I protect my path. What is mine belongs to me.",
    "One slow breath with the hand still. Then rise."]),
  "Did the day feel different on the other side of ten sealed seconds?"),

 (0, "Tea Like a Ceremony",
  "The cup is small so that you will look at it.",
  ["In the monastery, tea was never a drink. It was a clock that measured attention. A visitor who drank in one gulp was listened to politely and taught nothing, not from cruelty, but because there was nowhere in him for anything to land.",
   "Today, one cup, taken slowly, no phone within reach. Watch the steam. Feel the heat move into your hands. Taste the first sip as if you will be asked to describe it. That is the whole practice. It sounds like nothing. So does a key turning in a lock."],
  ("Today's practice, ten minutes",
   ["Make one hot drink with full attention: the water, the pour, the colour changing.",
    "Sit with it somewhere without a screen. Hold the cup with both hands.",
    "Drink it slower than feels natural. When you finish, sit for one breath more."]),
  "What did you notice in the cup that you have never noticed before?"),

 (0, "The Seventh Morning",
  "Rest is also a practice. Perhaps the hardest one.",
  ["Six days of practice are behind you. Today you add nothing.",
   "Repeat only what has already become yours: the four sentences, or the sealed ten seconds, or the slow cup. Choose one. Let the others rest. A path is not built by walking all of it every day.",
   "Notice, tonight, which practice you missed when you skipped it. That longing is information. It tells you which door is yours."],
  ("Today's practice, your choice",
   ["Pick the one practice from this week that felt most like yours.",
    "Do only that one, with a little more care than usual.",
    "Before sleep, read your six journal lines from this week, slowly."]),
  "Which practice would you defend if someone tried to take it from you?"),

 # ---- WEEK 2 · THE BODY ----
 (1, "Stand on Salt",
  "Salt has never been just for food.",
  ["Spread a thick layer of coarse salt on the floor. Step onto it barefoot, and just stand still.",
   "Feel the grains press into your soles. The soles of your feet are among the most sensitive surfaces of the body, and thousands of nerve endings wake at once. Your attention drops out of your racing head and lands, fully, in your feet. Shoulders soften. Breath slows.",
   "In our monastery, salt marked a boundary: between the day that has gathered and the night that deserves better. Ten quiet minutes. That is the whole practice. The salt brings you into your body. Keeping the calm after you step off, that is the deeper art, and it is what the rest of this book is for."],
  ("Today's practice, ten minutes",
   ["In the evening, spread a tray or towel with a thick layer of coarse salt.",
    "Stand on it barefoot, still, eyes soft or closed. Let the feet report everything.",
    "When ten minutes pass, step off, brush your feet, and go to bed without a screen."]),
  "What did your feet tell you that your head had been too loud to hear?"),

 (1, "Wash What You Carried",
  "The hands touch everything the day contains. Let them end it clean.",
  ["Tonight, wash your hands slowly, with intention, as the last act of the day. Not the quick rinse of habit. Water as warm as comfort allows, and while the water runs over your hands, say quietly: what I carried today, I set down.",
   "You shook hands, held a phone full of arguments, gripped a wheel in traffic, held your own face in worry. The hands were present for all of it. Ending the day by deliberately washing them is a way of telling the whole body: it is finished, you may stop carrying it.",
   "No claim here about energy you must believe. The claim is smaller and harder: you will not be able to do this slowly, saying those words, while still rehearsing the argument from noon. The ritual crowds the rumination out. That is enough."],
  ("Today's practice, three minutes",
   ["Last thing before bed, run warm water. Wash slowly: palms, backs, each finger.",
    "While the water runs, say quietly: what I carried today, I set down.",
    "Dry your hands with care, as if they belonged to someone you love. They do."]),
  "What was the hardest thing to set down tonight?"),

 (1, "One Meal in Silence",
  "The body knows how to eat. It is rarely allowed to.",
  ["Choose one meal today and give it silence. No screen, no reading, no conversation. Just you and the food, and the strange loudness of your own chewing, which will embarrass you for exactly two minutes and then become peaceful.",
   "Eat slower than usual. Put the fork down between bites, not as a diet trick, but as a courtesy to the meal. Notice when the body says enough. It says it quietly, and it says it earlier than the mind, which eats for other reasons: boredom, comfort, the clock.",
   "One silent meal will not change your body. It will show you how rarely you are present for what keeps you alive. That is worth seeing once a day."],
  ("Today's practice, one meal",
   ["Pick the meal where silence is realistic. Remove the screen from the table entirely.",
    "Eat slowly. Set the fork down between bites. Taste each one as if reporting to a cook you respect.",
    "Stop when the body says enough, and sit one quiet minute before clearing the plate."]),
  "When did the body say enough, and did you listen?"),

 (1, "Walk Without Destination",
  "A walk with a purpose is an errand. A walk without one is a broom for the mind.",
  ["Today, walk for twenty minutes with no destination, no phone in your hand, no podcast in your ears. Yes, it will feel unproductive. That feeling is the point. You are teaching the mind that not every minute must earn its keep.",
   "Walk a little slower than your habit. Let the eyes rest on far things: rooftops, sky, the ends of streets. When a worry arrives, do not fight it. Let it walk beside you like a dog that will tire before you do. It always does."],
  ("Today's practice, twenty minutes",
   ["Leave the house with nothing in your hands. Phone silenced, in a pocket, or left behind.",
    "Walk without choosing a destination. Turn wherever the street looks quieter.",
    "Three times during the walk, notice something above eye level. Come home a slower person."]),
  "What did you see above eye level that you had walked past a hundred times?"),

 (1, "The Body Scan",
  "Tension hides where attention never visits.",
  ["Lie on your back tonight, on the bed or the floor, arms at your sides. You are going to visit your whole body, slowly, the way a caretaker walks a building at night, checking each door.",
   "Start at the feet. Rest your attention there until you can feel them without moving them. Then ankles, calves, knees, and upward, a few slow breaths in each place. When you find tension, and you will, in the jaw, the shoulders, the hands, do not order it to release. Just stay there, breathing, as if keeping it company. Held tension often lets go simply because someone finally came to look at it."],
  ("Today's practice, twelve minutes",
   ["Lie down, close your eyes, and bring attention to your feet until they feel warm and present.",
    "Move upward slowly: legs, belly, chest, hands, arms, shoulders, neck, jaw, forehead.",
    "Where you find holding, stay three extra breaths without forcing anything. Then move on."]),
  "Where does your body keep its secrets? You found at least one place tonight."),

 (1, "Cold Water, New Face",
  "The old day washes off. It was never attached.",
  ["Tomorrow morning, before the mirror gets a word in, cup cold water in your hands and press it to your face. Three times. Feel the shock, the cold spreading, the breath that catches and then deepens on its own.",
   "Cold water on the face does something simple and immediate: it interrupts. Whatever half-dream, half-dread the night assembled is broken mid-sentence, and for a moment there is only cold, skin, breath. In that gap you get to choose the first real thought of the day instead of inheriting one.",
   "My teacher called this washing yesterday's face off. He was not being poetic. He meant the face you made all yesterday, the held jaw, the audience face. It is not yours. Let it go down the drain."],
  ("Today's practice, one minute",
   ["On waking, go to the sink before the phone, before the mirror conversation.",
    "Press cold water to your face three times. Let the breath react however it wants.",
    "Look up at yourself once, briefly, and choose one word for the day. Just one."]),
  "What was your one word this morning, and did the day obey it?"),

 (1, "The Fourteenth Day",
  "Half the path is behind you. Look back once, then stop looking back.",
  ["Two weeks. Fourteen small doors, and you have opened most of them. Today, like every seventh day, you add nothing new.",
   "Read your journal lines from the first thirteen days. Read them slowly, as if a stranger wrote them, because in a sense one did: the person who began this book is not quite the person reading it now. The changes are small. They are supposed to be. A door does not need to move far to let different light in.",
   "Tonight, choose the one practice from this week that your body asked for again. The body votes honestly. Follow its vote."],
  ("Today's practice, your choice",
   ["Read all thirteen journal lines in one sitting, unhurried.",
    "Repeat the one bodily practice that left the deepest mark this week.",
    "Write tonight's line with the left side of the page: one sentence about who is showing up on day fourteen."]),
  "What has quietly changed that nobody else would notice yet?"),

 # ---- WEEK 3 · THE NOISE ----
 (2, "One Hour Without Input",
  "The mind is always eating. Today it fasts for one hour.",
  ["For one hour today: no phone, no music, no podcast, no book, no screen. Nothing coming in. You may walk, sit, cook, clean, stare out the window like people did for a hundred thousand years.",
   "The first twenty minutes are genuinely uncomfortable. The mind, denied its feed, will rattle the cage: remembered arguments, urgent nothings, a sudden need to check one thing. Let it rattle. You are not being cruel to it. You are letting silt settle in a jar of river water, and there is no way to hurry that except to stop shaking the jar.",
   "Somewhere in the back half of the hour, if you last, comes a particular quiet you may not have felt in years. That quiet is not empty. It is what your own company feels like."],
  ("Today's practice, one hour",
   ["Choose the hour in advance and tell anyone who needs to know you'll be unreachable.",
    "Phone in another room, powered off. Not silenced. Off.",
    "Do simple things with your hands, or nothing at all. Endure minute twenty. Meet minute fifty."]),
  "What arrived in the quiet after the rattling stopped?"),

 (2, "The Unsent Words",
  "Not every sentence you compose deserves a recipient.",
  ["Somewhere in you is a reply you have been drafting for days: to a comment, a message, a relative, a colleague. It rehearses itself while you shower. It sharpens itself while you try to sleep.",
   "Tonight, write it down, all of it, by hand if you can, as unfairly and completely as it wants to be written. Then do not send it. Fold the page. The point was never the recipient. The point was that the sentence was living in you rent-free, and writing is how you serve it notice.",
   "You will feel the difference immediately: a rehearsed grievance needs an audience to survive. On paper, folded, it has one reader, and that reader has already moved on."],
  ("Today's practice, fifteen minutes",
   ["Write the unsent reply in full. No fairness required. Paper if possible.",
    "Read it once. Notice which line you wrote for justice and which for applause.",
    "Fold it and put it away, or tear it. Both work. Sending it is the only failure."]),
  "Which line were you most proud of, and who was it really for?"),

 (2, "Spend Fewer Words",
  "The quiet man is not hiding. He is choosing.",
  ["Today, spend words like money you respect. Not silence, not sulking: economy. Before speaking, one small question: does this sentence improve on the silence it replaces?",
   "You will notice how much of your talk is filler thrown at discomfort, agreement performed to be liked, repetition of things everyone present already knows. Let those sentences die young. What survives is speech with weight, and people hear the difference immediately, though they cannot name it.",
   "In the monastery, the elder who spoke least was interrupted never. There is a lesson about supply and demand in that, but mostly there is a lesson about attention: yours, gathered instead of scattered."],
  ("Today's practice, all day",
   ["Before each non-essential sentence today, pause one beat. Speak only if it beats the silence.",
    "When listening, listen to the end. Do not build your reply while the other person is still speaking.",
    "Tonight, notice: were you lonelier for the missing words, or lighter?"]),
  "Which sentence did you not say today, and what happened instead?"),

 (2, "A Day Without News",
  "You were not built to grieve for the whole world before breakfast.",
  ["Today, no news. Not the apps, not the sites, not the radio in the car, not the headlines a friend recites at lunch, walk those to a different topic. One day.",
   "Understand what you are testing. Not whether the world matters. Whether being informed by the minute changes anything except your nervous system. If something truly great happens today, you will hear. The village always tells you when a fire is real. What the feed delivers is different: a thousand fires you cannot reach with any bucket.",
   "Tonight, ask what you actually missed. Usually the honest answer is: nothing that needed me, and several hours of low dread that never found a target."],
  ("Today's practice, one day",
   ["Remove or bury the news apps for twenty-four hours. Log out of what you cannot bury.",
    "When the urge to check arrives, name what you are actually looking for. It is rarely information.",
    "Spend one reclaimed moment on something within reach of your two hands."]),
  "What did you reach for instead, and was it better?"),

 (2, "Clean One Surface",
  "The state of the table is the state of the mind. Start with the table. It's easier.",
  ["Choose one surface you see every day: the kitchen table, the desk, the shelf by the door. Clear it completely. Wipe it. Put back only what belongs, and let belongs be a strict judge.",
   "Do not clean the house. That is a different day and a different mood. One surface, done entirely, beats a whole room done halfway, because what you are practicing is not tidiness. It is finishing. The mind rests differently in a room where one thing, even a small thing, is fully complete.",
   "Tomorrow morning that surface will greet you before anyone else does. Let one corner of your world say: handled."],
  ("Today's practice, fifteen minutes",
   ["Empty the chosen surface completely. Every object off. Wipe it clean.",
    "Return only what earns its place. Relocate or release the rest.",
    "Look at it once from across the room. Let the mind photograph it."]),
  "How did the cleared surface change the room, and what did it ask you to clear next?"),

 (2, "The Sound Beneath Sounds",
  "Silence is not the absence of sound. It is the room the sounds stand in.",
  ["Sit by an open window for ten minutes today and only listen. Do not name what you hear, or try not to: the naming machine is exactly what you are resting. A car is not a car. It is a swell, a fade. A bird is not a bird. It is three notes and a space.",
   "Behind the traffic and the neighbours and the fridge, there is something else: the room tone of the world, the quiet that all of it happens inside. You cannot hear it by straining. You hear it the way you see faint stars, by looking slightly away.",
   "This is the closest thing to the practice that named this book. Between two sounds, as between two thoughts, there is a gap. Nobody can live in the gap. But knowing it is there changes how loud everything else gets to be."],
  ("Today's practice, ten minutes",
   ["Sit by a window, eyes closed or soft. Hands still.",
    "For ten minutes, receive sounds without naming them. When you catch yourself labelling, let the label fall.",
    "In the last minute, listen for the quiet behind everything. Do not grasp at it. Just nod to it."]),
  "What did you hear when you stopped naming things?"),

 (2, "The Twenty-First Day",
  "Three weeks of small doors. The corridor behind you is longer than you think.",
  ["Rest day. You know the shape now: nothing new, one practice repeated, the week's journal lines read slowly.",
   "But add this, once: sit for a moment with how the noise treats you now. The phone in the other room, does it pull like it did on day one? The news, the unsent replies, the filler words. None of them are gone. They are quieter, or you are larger. It comes to the same thing.",
   "One week remains, and it is the deepest one. The first three weeks cleared the ground. The last one builds the room."],
  ("Today's practice, your choice",
   ["Repeat the week-three practice that cost you the most. The cost was the teaching.",
    "Read this week's journal lines. Notice which ones sound like a stranger already.",
    "Sleep early tonight if you can. Week four asks for mornings."]),
  "What is quieter now: the world, or your argument with it?"),

 # ---- WEEK 4 · THE STILLNESS ----
 (3, "Seven Grains of Rice",
  "Gratitude with empty hands is a speech. Gratitude with rice in them is a practice.",
  ["Tonight, count seven grains of rice into your palm. Look at them properly: each one was a plant, in a field, in weather, tended by someone whose name you will never know, carried by hands and roads and ships to arrive in your kitchen and be ignored.",
   "Place them in a small dish by the window, one at a time, and with each grain name one thing that fed you this year. Not the seven biggest things. The seven that come. A person, a meal, a morning, an apology, a job, a song, a stranger's patience in traffic.",
   "Leave the dish by the window overnight. In the morning, return the grains to the bag or give them to the birds. Gratitude is not a mood you wait for. It is a thing you do with your hands until the mood arrives, embarrassed to be late."],
  ("Today's practice, five minutes",
   ["Count seven grains of rice into your palm before bed.",
    "Place them one by one in a small dish, naming one nourishment per grain, aloud or silent.",
    "Leave the dish by the window overnight. In the morning, return or scatter them with thanks."]),
  "Which of the seven surprised you by coming to mind at all?"),

 (3, "Words to Your Mother",
  "Some words wait decades to travel one metre.",
  ["Today, say something true to someone who fed you, in whatever sense feeding took: a mother, a father, whoever stood in that place. If they are living, call. Not text. Voice. Tell them one specific thing you remember and never mentioned: the lunches, the waiting outside lessons, the coat given on a cold walk.",
   "If they are gone, or if the relationship is a wound, write the words instead, in your journal, addressed properly by name. The saying is for you as much as them. Unsaid gratitude hardens into a strange kind of grief that visits at odd hours. Said, even to a page, it becomes lighter and turns into something you can carry.",
   "You will know the right words because your voice will resist them slightly. Say them anyway. Nobody on this earth has ever regretted this practice for longer than the phone call took."],
  ("Today's practice, one call or one page",
   ["Choose the person. Choose one specific memory, small is better.",
    "Call, and tell them. Let the silence after land. Do not rush to fill it.",
    "If a call is impossible, write it as a letter in your journal, addressed by name."]),
  "What did you finally say, and what came back?"),

 (3, "The Letter You Will Not Send",
  "Forgiveness is not a gift to them. It is you, setting down a hot stone.",
  ["There is a name that still tightens your chest. You know it before I finish the sentence. Today you write to that name.",
   "Write what they did. Write what it cost you, honestly, without heroics. And then, only if it is true, write the sentence: I am tired of carrying this, and I am allowed to put it down. That is what forgiveness is. Not a verdict that what happened was acceptable. A decision about freight: that your hands have better things to hold.",
   "Do not send it. This letter has one reader. Some hurts will need this letter more than once, and that is not failure, it is how heavy things get moved: in stages, by one person, quietly."],
  ("Today's practice, twenty minutes",
   ["Write the letter by hand: what happened, what it cost, no performance.",
    "If true, end with: I am tired of carrying this, and I am allowed to put it down.",
    "Fold it away or destroy it. Notice your shoulders in the hour after."]),
  "What did carrying it cost you this year alone?"),

 (3, "Three Things Before Sleep",
  "End the day the way you would end a letter to someone you love.",
  ["Do not go to sleep without saying these three things, to God, to the sky, to whatever you trust to be larger than the day. The address matters less than the honesty.",
   "First: thank you for everything I did not understand today. The delays, the closed doors, the plans that failed. I do not need the whole map to trust the road. Second: I set down what I cannot control. Every fear, every weight, every what if. I am not taking them to bed; they have nowhere to sleep there. Third: give me peace tonight. Not just sleep. Peace. And let something in me remember, even while I rest, that good things are still quietly at work.",
   "Say them slowly. The night takes the shape of the last true thing you say into it."],
  ("Today's practice, two minutes",
   ["In bed, lights out, say the three things slowly: the thanks, the setting down, the asking.",
    "Between each one, a full breath.",
    "Let the last word be the last word. No phone after. The night begins there."]),
  "Which of the three was hardest to mean tonight?"),

 (3, "The Locked Door",
  "Everyone keeps one door locked and calls the key lost. The key is not lost.",
  ["There is a thing you have decided you cannot do, and the decision is old. Older than your reasons. Speak to strangers. Ask for the raise. Start the thing. Leave the thing. You call it not for me, and the door stays locked, and the key sits where you left it: in the small choice you make every time the door comes near.",
   "Tonight, take an old key, any key, and put it under your pillow. Folk practice, yes. But answer its question honestly before you sleep: which door? Not five doors. One. The first one that came to mind and was immediately talked over by the second.",
   "In the morning, hold the key for a moment and name one step small enough to take this week. Not through the door. Toward it. Doors that stayed shut for years rarely open in a day. They open the way they closed: one quiet decision at a time."],
  ("Today's practice, two minutes and one honest answer",
   ["Tonight, place an old key under or beside your pillow.",
    "Before sleep, name the one door. First answer counts, not the safest one.",
    "In the morning, key in hand, choose one step toward it small enough to survive your schedule."]),
  "Which door, and what is the step?"),

 (3, "Keep One Joy Private",
  "What is shown grows thin. What is kept grows roots.",
  ["Something good is happening to you, or beginning to. The modern reflex is to announce it while it is still soft, and let the applause decide if it is real. Today, practice the opposite: keep one good thing entirely to yourself. A plan, a hope, a small win, this whole strange month of practices. Tell no one, just for now.",
   "This is not secrecy from shame. It is a greenhouse. Young things need warmth more than weather, and attention, even kind attention, is weather. Watch what happens to a joy you do not spend: it stops performing and starts becoming.",
   "The old monks kept their deepest practices unannounced, not because the practices were fragile, but because the announcing self and the practicing self are rivals, and only one of them can hold the tool."],
  ("Today's practice, ongoing",
   ["Choose one good, growing thing and decide: this stays mine until it can stand.",
    "When the urge to share it arrives, notice what the sharing would be for.",
    "Spend that urge on the thing itself: one more step, made quietly."]),
  "What are you letting grow in the dark, and how did it feel to not spend it?"),

 (3, "The Quiet Between Thoughts",
  "You are not the voice. You are the one who hears it.",
  ["Sit today for fifteen minutes and watch thoughts the way you watched sounds at the window: arriving, swelling, fading. Do not fight them, follow them, or grade them. Just notice each one begin and, more important, notice each one end.",
   "Because they do end. And between the end of one and the start of the next there is a gap. It is short. It does not matter that it is short. In that gap there is no commentary, no argument, no past, no rehearsal, and yet you are entirely there. That is the quiet this book is named for. It has been in you all along, between every two thoughts you have ever had, waiting like a pause in music that makes the music bearable.",
   "You cannot widen the gap by force. You widen it by acquaintance. Every time you notice it, it becomes slightly easier to find, the way a path through grass becomes a path by being walked.",
   "This is the whole teaching. Everything else in these thirty days was a way of walking you here."],
  ("Today's practice, fifteen minutes",
   ["Sit comfortably, eyes closed. Let the breath settle without managing it.",
    "Watch each thought arrive and end. Do not push. Attend especially to the endings.",
    "When you notice the gap, do not pounce on it. Nod to it, and let the next thought come."]),
  "You found the gap, or the gap found you. What was it like?"),

 (3, "Build Your Own Morning",
  "The student copies the recipe. The cook tastes and decides.",
  ["Twenty-eight days of practices are behind you, and by now your body has voted. Some practices it asks for. Some it merely tolerated. Today you stop being a student of my mornings and become the author of yours.",
   "Choose three: one for waking, one for the middle of the day, one for the edge of sleep. Only rules: the waking one comes before the phone, the sleeping one comes after it, and all three must be small enough to survive your worst day, because a practice that only fits good days is a decoration.",
   "Write your liturgy in the journal, in ink, as three plain lines. This page will outlast the book."],
  ("Today's practice, one page",
   ["Review your journal lines and mark the practices your body asked to repeat.",
    "Choose three: morning, midday, night. Small enough for your worst day.",
    "Write them as three lines and put tomorrow's first one somewhere you will trip over it."]),
  "What are your three lines?"),

 (3, "The Thirtieth Day",
  "The book ends. The mornings continue.",
  ["Thirty days ago your mind was loud, and you suspected it did not have to be. You were right. Not because the noise is gone. Because you now hold a handful of small doors, and you know from your own hand, not from my telling, that each of them opens.",
   "Read your thirty journal lines today, start to finish. That is the real book. The one I wrote just kept you company while you wrote it.",
   "Keep your three-line liturgy. Return to any chapter when its door sticks. And when someone you love says, half joking, that their mind will not stop talking, you will know what to hand them, and you will know, quietly, that it works. Go gently. The path does not resent slow walkers. Peace be with you, my friend."],
  ("Today's practice, and tomorrow's",
   ["Read all thirty journal lines in one unhurried sitting.",
    "Do your three-line liturgy exactly as written.",
    "Tomorrow morning: line one, before the world enters. That is day thirty-one. They are all day thirty-one now."]),
  "What would you tell the person who opened this book thirty days ago?"),
]

HEAD = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  @page { size: 6in 9in; margin: 0; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: Georgia, 'Times New Roman', serif; color: #2b2620; background: #faf6ee; }
  .page { width: 6in; height: 9in; padding: 0.85in 0.8in; page-break-after: always; position: relative; background: #faf6ee; overflow: hidden; }
  .cover { padding: 0; background: #12100d; color: #efe7d6; }
  .cover img { width: 100%; height: 62%; object-fit: cover; object-position: top; opacity: 0.92; }
  .cover .block { padding: 0.45in 0.6in; text-align: center; }
  .cover h1 { font-size: 30px; font-weight: normal; letter-spacing: 0.06em; line-height: 1.25; }
  .cover .rule { width: 0.9in; border-top: 1px solid #a08a5f; margin: 0.16in auto; }
  .cover .sub { font-size: 12.5px; letter-spacing: 0.18em; text-transform: uppercase; color: #c9b286; }
  .cover .author { margin-top: 0.22in; font-size: 14px; letter-spacing: 0.12em; }
  h2.week { font-size: 13px; letter-spacing: 0.28em; text-transform: uppercase; color: #8a6d3f; text-align: center; }
  .daynum { font-size: 58px; color: #d9c9a6; text-align: center; line-height: 1; margin-top: 0.08in; }
  h3.daytitle { font-size: 20px; font-weight: normal; text-align: center; margin: 0.1in 0 0.04in; }
  .epigraph { font-style: italic; text-align: center; color: #6f6353; font-size: 12px; margin-bottom: 0.22in; }
  p { font-size: 12px; line-height: 1.66; margin-bottom: 0.11in; text-align: justify; }
  p.first::first-letter { font-size: 30px; float: left; line-height: 0.9; padding-right: 6px; color: #8a6d3f; }
  .practice { border-top: 1px solid #d9c9a6; border-bottom: 1px solid #d9c9a6; padding: 0.13in 0.05in; margin: 0.16in 0; }
  .practice .label { font-size: 10px; letter-spacing: 0.22em; text-transform: uppercase; color: #8a6d3f; margin-bottom: 0.08in; }
  .practice ol { margin-left: 0.24in; }
  .practice li { font-size: 11.5px; line-height: 1.58; margin-bottom: 0.05in; }
  .journal { margin-top: 0.14in; }
  .journal .label { font-size: 10px; letter-spacing: 0.22em; text-transform: uppercase; color: #8a6d3f; }
  .journal p { font-style: italic; color: #6f6353; }
  .rule-line { border-bottom: 1px dotted #c8b795; height: 0.3in; }
  .motif { display: block; width: 1.1in; margin: 0.2in auto 0; }
  .folio { position: absolute; bottom: 0.38in; left: 0; right: 0; text-align: center; font-size: 10px; color: #a4906a; letter-spacing: 0.2em; }
  .titlepage { text-align: center; padding-top: 2.1in; }
  .titlepage h1 { font-size: 26px; font-weight: normal; letter-spacing: 0.05em; }
  .titlepage .sub { font-size: 12px; letter-spacing: 0.2em; text-transform: uppercase; color: #8a6d3f; margin-top: 0.14in; }
  .titlepage img { width: 1.4in; margin-top: 0.55in; }
  .titlepage .author { margin-top: 0.5in; font-size: 13px; letter-spacing: 0.1em; }
  .weekpage { text-align: center; padding-top: 2.6in; }
  .weekpage .wk { font-size: 13px; letter-spacing: 0.3em; text-transform: uppercase; color: #8a6d3f; }
  .weekpage h1 { font-size: 30px; font-weight: normal; margin-top: 0.12in; }
  .weekpage img { width: 1.7in; margin-top: 0.5in; }
</style></head><body>
"""


def day_page(i, d, folio):
    wk, title, epi, paras, (plabel, steps), journal = d
    parts = []
    if i == 0 or DAYS[i - 1][0] != wk:
        w = W[wk]
        parts.append(f'<div class="page weekpage"><div class="wk">{w[0]}</div>'
                     f'<h1>{w[1]}</h1><img src="{w[2]}"></div>')
    ps = "".join(f'<p class="{"first" if j == 0 else ""}">{p}</p>'
                 for j, p in enumerate(paras))
    steps_html = "".join(f"<li>{s}</li>" for s in steps)
    parts.append(
        f'<div class="page"><div class="daynum">{i + 1}</div>'
        f'<h3 class="daytitle">{title}</h3><p class="epigraph">{epi}</p>{ps}'
        f'<div class="practice"><div class="label">{plabel}</div><ol>{steps_html}</ol></div>'
        f'<div class="journal"><div class="label">One Line Tonight</div><p>{journal}</p>'
        f'<div class="rule-line"></div></div><div class="folio">{folio}</div></div>')
    return "".join(parts)


def build():
    html = [HEAD]
    html.append('<div class="page cover"><img src="cover_portrait.png"><div class="block">'
                '<div class="sub">A thirty-day return to</div><h1>The Quiet Between<br>Thoughts</h1>'
                '<div class="rule"></div><div class="author">MASTER KAION</div></div></div>')
    html.append('<div class="page titlepage"><h1>The Quiet Between Thoughts</h1>'
                '<div class="sub">Thirty days of small practices<br>for a mind that will not stop talking</div>'
                '<img src="ink_enso.png"><div class="author">Master Kaion</div>'
                '<div class="folio">This book accompanies a practice. It replaces no doctor and no medicine.</div></div>')
    html.append('<div class="page"><h2 class="week">Before You Begin</h2><img class="motif" src="ink_teacup.png">'
                '<p class="first">You did not find this book because your life is broken. You found it because your mind is loud, and you suspect it does not have to be.</p>'
                '<p>I spent forty years learning one thing in silence: peace is not found by changing where you live. It is found by changing how you meet your own mind. That sentence is easy to read and slow to learn. The thirty days in this book are how I teach it.</p>'
                '<p>Each day asks for ten minutes, sometimes less. One short teaching. One small practice. One line to write. That’s all. Don’t read ahead. A day read in one minute does nothing; a day lived changes the next one.</p>'
                '<p>Some practices will feel too simple to matter. Do them anyway. A glass of water beside a bed is a small thing. So is a single match in a dark room.</p>'
                '<p>If you miss a day, you have not failed. Begin again where you stopped. The path does not resent slow walkers. It only asks that you keep walking.</p>'
                '<div class="folio">3</div></div>')
    folio = 5
    for i, d in enumerate(DAYS):
        html.append(day_page(i, d, folio))
        folio += 1
    html.append('<div class="page titlepage"><h1>Go gently.</h1>'
                '<div class="sub">If this book gave you one quieter morning,<br>hand it to someone whose mind is loud.</div>'
                '<img src="ink_enso.png"><div class="folio">© Master Kaion · The Quiet Between Thoughts</div></div>')
    html.append("</body></html>")
    os.makedirs(BOOK, exist_ok=True)
    out = os.path.join(BOOK, "book.html")
    open(out, "w").write("".join(html))
    # manuscript json for the audiobook build
    json.dump({"weeks": [{"n": w[0], "t": w[1]} for w in W],
               "days": [{"week": d[0], "title": d[1], "epigraph": d[2],
                         "paras": d[3], "practice_label": d[4][0],
                         "steps": d[4][1], "journal": d[5]} for d in DAYS]},
              open(os.path.join(BOOK, "manuscript.json"), "w"), indent=1)
    words = sum(len(" ".join(d[3]).split()) + len(" ".join(d[4][1]).split()) for d in DAYS)
    print(f"book.html written · {len(DAYS)} days · ~{words} words of body text")


if __name__ == "__main__":
    build()
