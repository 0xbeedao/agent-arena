import json

from agentarena.util import response_parsers

# Dummy extract_fenced_code_block for test context if needed
# from llm.utils import extract_fenced_code_block


def test_extract_text_response_basic():
    data = json.dumps({"data": json.dumps({"data": "hello world"})})
    assert response_parsers.extract_text_response(data) == "hello world"


def test_extract_text_response_no_nested_data():
    data = json.dumps({"data": json.dumps({"foo": "bar"})})
    assert response_parsers.extract_text_response(data) == {"foo": "bar"}


def test_extract_fenced_json_valid_json():
    obj = {"a": 1}
    raw = json.dumps(obj)
    assert response_parsers.extract_obj_from_json(raw) == obj


def test_extract_fenced_json_invalid_json_with_fence(monkeypatch):
    raw = """```json\n{"b":2\n```"""
    assert response_parsers.extract_obj_from_json(raw) == None


def test_extract_fenced_json_invalid_json_no_fence(monkeypatch):
    monkeypatch.setattr(response_parsers, "extract_fenced_code_block", lambda s: None)
    raw = "not a json"
    result = response_parsers.extract_obj_from_json(raw)
    assert result is None


def test_extract_fenced_json_real_example():
    raw = """
```json\\n{\"action\": \"move\", \"target\": \"5,5\", \"narration\": \"Maia charges towards the flag, eyes locked on the Spectral Standard. The crowd\\'s cheers fuel her determination as she navigates the castle courtyard.\", \"memories\": \"Remember the flag\\'s location at 5,5 and the presence of other players and features like the Beweaponed Balustrade and Treacherous Tapestry.\"}\\n```
"""
    result = response_parsers.extract_obj_from_json(raw)
    assert result == {
        "action": "move",
        "target": "5,5",
        "narration": "Maia charges towards the flag, eyes locked on the Spectral Standard. The crowd's cheers fuel her determination as she navigates the castle courtyard.",
        "memories": "Remember the flag's location at 5,5 and the presence of other players and features like the Beweaponed Balustrade and Treacherous Tapestry.",
    }


def test_parse_list_simple():
    assert response_parsers.parse_list([1, 2, 3]) == [1, 2, 3]


def test_parse_list_dict_with_data():
    assert response_parsers.parse_list({"data": [4, 5]}) == [4, 5]


def test_parse_list_json_string():
    assert response_parsers.parse_list("[6,7]") == [6, 7]


def test_parse_list_nested_json_string():
    raw = json.dumps({"data": "[8,9]"})
    assert response_parsers.parse_list(json.loads(raw)) == [8, 9]


def test_parse_list_empty_string():
    assert response_parsers.parse_list("") == []


def test_parse_list_string_with_brackets():
    s = "foo [10, 11, 12] bar"
    assert response_parsers.parse_list(s) == [10, 11, 12]


def test_parse_list_fenced_code(monkeypatch):
    monkeypatch.setattr(response_parsers, "extract_obj_from_json", lambda s: "[13,14]")
    s = "```[13,14]```"
    assert response_parsers.parse_list(s) == [13, 14]


def test_parse_list_invalid_json():
    assert response_parsers.parse_list("not a list") == []


def test_parse_list_json_decode_error(monkeypatch):
    # Simulate extract_fenced_json raising error
    monkeypatch.setattr(
        response_parsers, "extract_obj_from_json", lambda s: "not a list"
    )
    assert response_parsers.parse_list("not a list") == []


# def test_extract_obj_from_json_real_example():
#     raw = """{\"data\":\"Hear ye, hear ye! Welcome, esteemed guests and valiant players, to the most spectacular contest in all the land! \\\\n\\\\nI present to you... the \\\\\"Flag Castle\\\\\" arena! *excited cheering from the crowd*\\\\n\\\\nThis 10 x 10 battleground is set in a grand castle courtyard, with stone walls towering above and a view of the vast Kingdom beyond. The ever-fickle cheering crowd watches from on high, sure to provide a tough and distracting atmosphere! And oh boy, do we have an esteemed & vibrant crowd today. They might just be louder than the player\\'s screaming as the other team mercilessly hunts them down.\\\\n\\\\nIn this classic game of Capture the Flag, two teams will face off: \\\\n\\\\nTeam 1: The Valiant Victors\\\\nLed by their fearless flagkeepers, they\\'ll be defending the honor of the Kingdom!\\\\n\\\\nAnd Team 2: The Daring Defilers \\\\nThe invading upstarts trying to seize our precious banner! The match is simple: Bring the enemy flag to your base and claim victory.\\\\n\\\\nThis arena features many obstacles to avoid and strategy points to consider, including flag\\'s location at 5,5\\', the defensible base at 1,5\\', Vibrant Slumber Spores at 8,8\\', a grand Weeping Gargoyle Fountain right next to the flag, and - other notable strategic points:\\\\n\\\\n- Collapsed Crenellation at 3,2\\'\\\\n- Knight-Commander\\'s Empty Armor at 2,8\\' \\\\n- Moldy Stable Bales at 7,3\\'\\\\n- Sun-Bleached Royal Standard winding its way to 5,10\\'\\\\n- Abandoned Siege Ladder at 9,4\\' (Maybe they could\\'ve used this to get a better view of the match Comic crowd)\\\\n\\\\nOutwitting your opponents, using your surroundings to your advantage, and a little bit of luck with player distribution will all be key to securing that sweet, sweet victory these players so desperately crave. But let\\'s see if luck and skill will guide them to buy their SunStone while seizing the other team\\'s standard.\\\\n\\\\nSo place your bets, fill the arena with your cheers, and let us begin! May the best team win fodder for my side-splitting jokes!\",\"job_id\":\"cruel-even-Thing-Wasnt-pie\",\"message\":null,\"state\":\"complete\"}"""
#     result = response_parsers.extract_obj_from_json(raw)
#     assert result == {
#         "data": "Hear ye, hear ye! Welcome, esteemed guests and valiant players, to the most spectacular contest in all the land! \\n\\nI present to you... the \\\"Flag Castle\\\" arena! *excited cheering from the crowd*\\n\\nThis 10 x 10 battleground is set in a grand castle courtyard, with stone walls towering above and a view of the vast Kingdom beyond. The ever-fickle cheering crowd watches from on high, sure to provide a tough and distracting atmosphere! And oh boy, do we have an esteemed & vibrant crowd today. They might just be louder than the player's screaming as the other team mercilessly hunts them down.\\n\\nIn this classic game of Capture the Flag, two teams will face off: \\n\\nTeam 1: The Valiant Victors\\nLed by their fearless flagkeepers, they'll be defending the honor of the Kingdom!\\n\\nAnd Team 2: The Daring Defilers \\nThe invading upstarts trying to seize our precious banner! The match is simple: Bring the enemy flag to your base and claim victory.\\n\\nThis arena features many obstacles to avoid and strategy points to consider, including flag's location at 5,5', the defensible base at 1,5', Vibrant Slumber Spores at 8,8', a grand Weeping Gargoyle Fountain right next to the flag, and - other notable strategic points:\\n\\n- Collapsed Crenellation at 3,2'\\n- Knight-Commander's Empty Armor at 2,8' \\n- Moldy Stable Bales at 7,3'\\n- Sun-Bleached Royal Standard winding its way to 5,10'\\n- Abandoned Siege Ladder at 9,4' (Maybe they could've used this to get a better view of the match Comic crowd)\\n\\nOutwitting your opponents, using your surroundings to your advantage, and a little bit of luck with player distribution will all be key to securing that sweet, sweet victory these players so desperately crave. But let's see if luck and skill will guide them to buy their SunStone while seizing the other team's standard.\\n\\nSo place your bets, fill the arena with your cheers, and let us begin! May the best team win fodder for my side-splitting jokes!",
#         "job_id": "cruel-even-Thing-Wasnt-pie",
#         "message": None,
#         "state": "complete",
#     }


def test_extract_list_from_json_string():
    raw = """
[...]

[
  {
    "name": "Jester's Jape",
    "description": "A collection of colorful juggling balls with precious gems embedded in them. Players can use these to gleefully distract and blind opponents, gaining a brief advantage to escape or steal the flag.",
    "position": "5,5"
  }, 
  {
    "name": "Widower's Willow",
    "description": "A weeping willow tree with long, thin branches. The leaves rustle enticingly and players are tempted to reach out and touch. However, the branches will ensnare a player, trapping them in place until another player touches the trunk to set them free.",
    "position": "2,8"
  },
  {
    "name": "Enchanted Igloo",
    "description": "A small, shimmering handmade shelter. Players can use it as temporary cover. If they shelter inside it, healing powers of the mountain air temporarily reduce their damage taken by 20%.",
    "position": "6,3"
  },
  {
    "name": "Flirty Fountain",
    "description": "An ornate and attractive outdoor h2o feature that invites players closer. It's running from a trickling bubbly top all the way to a curvy ornate bottom rim. Players can drink from it to gain a short time invincibility. However, while invincible, the player will lose control and run around erratically for a short time.",
    "position": "7,6"
  },
  {
    "name": "Moonbeams",
    "description": "Glowing moonlight beams emanating from a faintly hidden outdoor lantern. The beams pierce through the shadows on the ground and hint at a possible path for players to silently and sneakily approach flags. It serves as an info-gathering tool to surveil areas.",
    "position": "3,2"
  }
]
"""
    result = response_parsers.parse_list(raw)
    assert result is not None
    assert result == [
        {
            "name": "Jester's Jape",
            "description": "A collection of colorful juggling balls with precious gems embedded in them. Players can use these to gleefully distract and blind opponents, gaining a brief advantage to escape or steal the flag.",
            "position": "5,5",
        },
        {
            "name": "Widower's Willow",
            "description": "A weeping willow tree with long, thin branches. The leaves rustle enticingly and players are tempted to reach out and touch. However, the branches will ensnare a player, trapping them in place until another player touches the trunk to set them free.",
            "position": "2,8",
        },
        {
            "name": "Enchanted Igloo",
            "description": "A small, shimmering handmade shelter. Players can use it as temporary cover. If they shelter inside it, healing powers of the mountain air temporarily reduce their damage taken by 20%.",
            "position": "6,3",
        },
        {
            "name": "Flirty Fountain",
            "description": "An ornate and attractive outdoor h2o feature that invites players closer. It's running from a trickling bubbly top all the way to a curvy ornate bottom rim. Players can drink from it to gain a short time invincibility. However, while invincible, the player will lose control and run around erratically for a short time.",
            "position": "7,6",
        },
        {
            "name": "Moonbeams",
            "description": "Glowing moonlight beams emanating from a faintly hidden outdoor lantern. The beams pierce through the shadows on the ground and hint at a possible path for players to silently and sneakily approach flags. It serves as an info-gathering tool to surveil areas.",
            "position": "3,2",
        },
    ]
