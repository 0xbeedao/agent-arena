PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE llmmodel (
	id VARCHAR NOT NULL, 
	created_at INTEGER, 
	updated_at INTEGER, 
	name VARCHAR NOT NULL, 
	model_id VARCHAR NOT NULL, 
	canonical_id VARCHAR, 
	active BOOLEAN NOT NULL, 
	notes VARCHAR, 
	supports_json BOOLEAN NOT NULL, 
	supports_schema BOOLEAN NOT NULL, 
	score INTEGER NOT NULL, 
	PRIMARY KEY (id)
);
INSERT INTO llmmodel VALUES('Needy-CLOSE-walk-Half-Pros',1752614406,1752614406,'aion','openrouter/aion-labs/aion-1.0','aion-labs/aion-1.0',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('taste-Water-WHARF-street-Toe',1752614406,1752614406,'aion-mini','openrouter/aion-labs/aion-1.0-mini','aion-labs/aion-1.0-mini',1,'',0,0,0);
INSERT INTO llmmodel VALUES('bitter-RECENT-Weapon-Limit-DREARY',1752614406,1752614406,'aion-rp','openrouter/aion-labs/aion-rp-llama-3.1-8b','aion-labs/aion-rp-llama-3.1-8b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('verbs-Jail-Awful-Wing-doll',1752614406,1752614406,'anubis','openrouter/thedrummer/anubis-pro-105b-v1','thedrummer/anubis-pro-105b-v1',1,'',0,0,0);
INSERT INTO llmmodel VALUES('spotty-Cobweb-Chief-Beef-Nuclei',1752614406,1752614406,'celeste','openrouter/nothingiisreal/mn-celeste-12b','nothingiisreal/mn-celeste-12b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('peace-Window-Joys-dirty-SIMPLE',1752614406,1752614406,'chatgpt','gpt-3.5-turbo','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('FLASH-Misco-side-bent-Claim',1752614406,1752614406,'chatgpt-16k','3.5-16k,gpt-3.5-turbo-16k','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('USEFUL-FALCON-ELATED-puffy-Real',1752614406,1752614406,'chatgpt-4o','chatgpt-4o-latest','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('beos-Echo-DIRT-liquid-Bronze',1752614406,1752614406,'claude-3.5','openrouter/anthropic/claude-3.7-sonnet','anthropic/claude-3-7-sonnet-20250219',0,'Model is too expensive, disabled by system',0,1,10);
INSERT INTO llmmodel VALUES('BIKE-Wave-diver-Ting-Engine',1752614406,1752614406,'claude-sonnet-4','openrouter/anthropic/claude-sonnet-4','anthropic/claude-4-sonnet-20250522',0,'Model is too expensive, disabled by system',0,1,10);
INSERT INTO llmmodel VALUES('DRAWER-AMOUNT-Water-Romano-cloth',1752614406,1752614406,'clauee-opus-4','openrouter/anthropic/claude-opus-4','anthropic/claude-4-opus-20250522',0,'Model is too expensive, disabled by system',0,1,10);
INSERT INTO llmmodel VALUES('TACIT-Roll-Blaze-PAN-Expect',1752614406,1752614406,'command-a','openrouter/cohere/command-a','cohere/command-a-03-2025',0,'Model is too expensive, disabled by system',1,0,10);
INSERT INTO llmmodel VALUES('mice-corn-ABRUPT-Ask-BEEF',1752614406,1752614406,'deepcoder','openrouter/agentica-org/deepcoder-14b-preview:free','agentica-org/deepcoder-14b-preview',1,'',0,0,0);
INSERT INTO llmmodel VALUES('Cold-HAIR-Warmth-Add-Mask',1752614406,1752614406,'deepseek','openrouter/deepseek/deepseek-chat-v3-0324','deepseek/deepseek-chat-v3-0324',1,'',1,1,20);
INSERT INTO llmmodel VALUES('PRION-SUMMER-blush-Test-Scarf',1752614406,1752614406,'deepseek-free','openrouter/deepseek/deepseek-chat-v3-0324:free','deepseek/deepseek-chat-v3-0324',1,'',0,1,10);
INSERT INTO llmmodel VALUES('amused-Strap-SHAGGY-Zebra-YORUBA',1752614406,1752614406,'deepseek-r1','deepseek-r1:8b','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('Houses-potato-Cruel-Bumper-Ting',1752614406,1752614406,'dolphin3','dolphin3:latest','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('SIDER-Amount-Unit-Debt-CAPPS',1752614406,1752614406,'dolphin-24','openrouter/cognitivecomputations/dolphin3.0-r1-mistral-24b:free','cognitivecomputations/dolphin3.0-r1-mistral-24b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('VERSE-groan-hydro-CYRIL-CLOSED',1752614406,1752614406,'drummer','openrouter/thedrummer/valkyrie-49b-v1','thedrummer/valkyrie-49b-v1',1,'',1,0,10);
INSERT INTO llmmodel VALUES('pink-tempo-Part-MARKED-Third',1752614406,1752614406,'euryale','openrouter/sao10k/l3.3-euryale-70b','sao10k/l3.3-euryale-70b-v2.3',1,'',1,0,10);
INSERT INTO llmmodel VALUES('PURE-Rein-Marine-Frog-annan',1752614406,1752614406,'euryale-3.1','openrouter/sao10k/l3.1-euryale-70b','sao10k/l3.1-euryale-70b',1,'',1,0,10);
INSERT INTO llmmodel VALUES('love-Look-rejoin-ace-nosy',1752614406,1752614406,'eva','openrouter/eva-unit-01/eva-llama-3.33-70b','eva-unit-01/eva-llama-3.33-70b',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('vigor-Siding-Corn-salary-Broth',1752614406,1752614406,'eva-qwen','openrouter/eva-unit-01/eva-qwen-2.5-32b','',0,'Model is no longer available in OpenRouter API',0,0,0);
INSERT INTO llmmodel VALUES('rejoin-FRAIL-Injure-Bow-Tub',1752614406,1752614406,'fimbulvetr','openrouter/sao10k/fimbulvetr-11b-v2','sao10k/fimbulvetr-11b-v2',1,'',0,0,0);
INSERT INTO llmmodel VALUES('SUIT-tyra-cloth-Luck-Wire',1752614406,1752614406,'gemini-2.5-flash','openrouter/google/gemini-2.5-flash','google/gemini-2.5-flash',1,'',1,1,20);
INSERT INTO llmmodel VALUES('MANDA-Digi-fseek-memory-Dime',1752614406,1752614406,'gemini-2.5-pro','openrouter/google/gemini-2.5-pro','google/gemini-2.5-pro',1,'',1,1,20);
INSERT INTO llmmodel VALUES('war-SNAKE-car-Snakes-Elf',1752614406,1752614406,'gemini2-5-thinking','openrouter/google/gemini-2.5-flash-preview:thinking','',0,'Model is no longer available in OpenRouter API',0,0,0);
INSERT INTO llmmodel VALUES('FIT-Cloth-file-jeans-Hall',1752614406,1752614406,'glm-32b','openrouter/thudm/glm-z1-32b:free','thudm/glm-z1-32b-0414',1,'',0,0,0);
INSERT INTO llmmodel VALUES('quick-toric-KRAZY-dress-Bluey',1752614406,1752614406,'gpt-4.5','gpt-4.5-preview','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('FAINT-Fetch-Steam-Jeux-IDOL',1752614406,1752614406,'gpt4','gpt-4','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('VESSEL-MUON-Gifted-Mark-BURY',1752614406,1752614406,'gpt4.1','openrouter/openai/gpt-4.1','openai/gpt-4.1-2025-04-14',0,'Model is too expensive, disabled by system',1,1,20);
INSERT INTO llmmodel VALUES('Quack-shame-Twig-stmt-TOMMY',1752614406,1752614406,'gpt4.1-mini','openrouter/openai/gpt-4.1-mini','openai/gpt-4.1-mini-2025-04-14',1,'',1,1,20);
INSERT INTO llmmodel VALUES('Label-setenv-PLANTS-Equal-ULTIMO',1752614407,1752614407,'gpt4.1-nano','openrouter/openai/gpt-4.1-nano','openai/gpt-4.1-nano-2025-04-14',1,'',1,1,20);
INSERT INTO llmmodel VALUES('Stuff-Fancy-Craven-Saber-sore',1752614407,1752614407,'gpt4o','gpt-4o','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('FOREST-POISED-inform-story-awful',1752614407,1752614407,'gpt4o-mini','gpt-4o-mini','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('sign-Order-overt-Two-grey',1752614407,1752614407,'grok3','openrouter/x-ai/grok-3','x-ai/grok-3',0,'Model is too expensive, disabled by system',1,1,20);
INSERT INTO llmmodel VALUES('TIDY-AXONS-Glover-range-seed',1752614407,1752614407,'grok3-mini','openrouter/x-ai/grok-3-mini','x-ai/grok-3-mini',1,'',1,1,20);
INSERT INTO llmmodel VALUES('family-Vast-large-lands-Bell',1752614407,1752614407,'haiku','openrouter/anthropic/claude-3.5-haiku','anthropic/claude-3-5-haiku',1,'',0,1,10);
INSERT INTO llmmodel VALUES('Loud-atomic-Seed-RELIC-Mighty',1752614407,1752614407,'hermes','openrouter/nousresearch/deephermes-3-llama-3-8b-preview:free','nousresearch/deephermes-3-llama-3-8b-preview',1,'',0,0,0);
INSERT INTO llmmodel VALUES('toad-blitz-Used-Sin-CRUX',1752614407,1752614407,'infermatic','openrouter/infermatic/mn-inferor-12b','infermatic/mn-inferor-12b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('gaping-TOAD-ULTRA-RHYME-Tall',1752614407,1752614407,'inflection','openrouter/inflection/inflection-3-pi','inflection/inflection-3-pi',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('cleric-Drum-NOUNS-PLANTS-Intend',1752614407,1752614407,'inflection-productivity','openrouter/inflection/inflection-3-productivity','inflection/inflection-3-productivity',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('angle-slap-Birth-permit-FAGAN',1752614407,1752614407,'kimi','openrouter/moonshotai/kimi-dev-72b:free','moonshotai/kimi-dev-72b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('SKIRT-pasted-wreck-Food-REEF',1752614407,1752614407,'kimi-thinking','openrouter/moonshotai/kimi-vl-a3b-thinking:free','moonshotai/kimi-vl-a3b-thinking',1,'',0,0,0);
INSERT INTO llmmodel VALUES('HYDRO-DAMAGE-EFFECT-Tray-dead',1752614407,1752614407,'liquid','openrouter/liquid/lfm-40b','liquid/lfm-40b',1,'',1,0,10);
INSERT INTO llmmodel VALUES('MILKY-Add-Jeux-HANDS-stay',1752614407,1752614407,'ll4-maverick','openrouter/meta-llama/llama-4-maverick','meta-llama/llama-4-maverick-17b-128e-instruct',1,'',1,1,20);
INSERT INTO llmmodel VALUES('Paper-border-Slim-Kettle-array',1752614407,1752614407,'ll4-scout','openrouter/meta-llama/llama-4-scout','meta-llama/llama-4-scout-17b-16e-instruct',1,'',1,1,20);
INSERT INTO llmmodel VALUES('STAMP-Benz-many-Faded-Maurer',1752614407,1752614407,'llama-3.3','openrouter/nvidia/llama-3.3-nemotron-super-49b-v1:free','',0,'Model is no longer available in OpenRouter API',0,0,0);
INSERT INTO llmmodel VALUES('STUPID-Pine-last-noord-elite',1752614407,1752614407,'llama-4-maverick','openrouter/meta-llama/llama-4-maverick:free','',0,'Model is no longer available in OpenRouter API',0,0,0);
INSERT INTO llmmodel VALUES('like-Hover-Telly-Earch-Lysis',1752614407,1752614407,'llama-4-scout','openrouter/meta-llama/llama-4-scout:free','',0,'Model is no longer available in OpenRouter API',0,0,0);
INSERT INTO llmmodel VALUES('deer-Serve-WITTY-parcel-Launch',1752614407,1752614407,'magistral-medium','openrouter/mistralai/magistral-medium-2506','mistralai/magistral-medium-2506',0,'Model is too expensive, disabled by system',1,1,20);
INSERT INTO llmmodel VALUES('land-LIVE-Tacit-BRIGHT-Rebel',1752614407,1752614407,'magistral-small','openrouter/mistralai/magistral-small-2506','mistralai/magistral-small-2506',1,'',1,1,20);
INSERT INTO llmmodel VALUES('Meat-DUBLIN-nerdy-Nerdy-narrow',1752614407,1752614407,'magnum','openrouter/anthracite-org/magnum-v4-72b','anthracite-org/magnum-v4-72b',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('mori-Boot-SORTS-burch-EMMET',1752614407,1752614407,'midnight-rose','openrouter/sophosympatheia/midnight-rose-70b','sophosympatheia/midnight-rose-70b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('expres-Pixie-MOVING-Visit-EARTHY',1752614407,1752614407,'minimax','openrouter/minimax/minimax-m1','minimax/minimax-m1',1,'',0,1,10);
INSERT INTO llmmodel VALUES('lace-Array-airing-Show-COOING',1752614407,1752614407,'mistral-small','openrouter/mistralai/mistral-small-3.1-24b-instruct:free','mistralai/mistral-small-3.1-24b-instruct-2503',1,'',1,1,20);
INSERT INTO llmmodel VALUES('PLACE-Bang-Travel-Earthy-tender',1752614407,1752614407,'o3','openrouter/openai/o3','openai/o3-2025-04-16',0,'Model is too expensive, disabled by system',1,1,20);
INSERT INTO llmmodel VALUES('MICE-NIPPLE-Lumpy-Admit-Club',1752614407,1752614407,'o3-hi','openrouter/openai/o3-mini-high','openai/o3-mini-high-2025-01-31',1,'',1,1,20);
INSERT INTO llmmodel VALUES('wound-CRAVEN-Rock-HELM-Fuzzy',1752614407,1752614407,'o4-hi','openrouter/openai/o4-mini-high','openai/o4-mini-high-2025-04-16',1,'',1,1,20);
INSERT INTO llmmodel VALUES('occur-Word-Gabby-HELP-slow',1752614407,1752614407,'o4-mini','openrouter/openai/o4-mini','openai/o4-mini-2025-04-16',1,'',1,1,20);
INSERT INTO llmmodel VALUES('gate-Errata-dohc-ABRUPT-Bite',1752614407,1752614407,'open-4o-mini','openrouter/openai/gpt-4o-mini','openai/gpt-4o-mini',1,'',1,1,20);
INSERT INTO llmmodel VALUES('bead-Kemp-AZTEC-Slow-stone',1752614407,1752614407,'qwen','openrouter/qwen/qwen-max','qwen/qwen-max-2025-01-25',0,'Model is too expensive, disabled by system',1,1,20);
INSERT INTO llmmodel VALUES('FLAG-Duarte-dwarf-Porter-wobble',1752614407,1752614407,'qwen3','qwen3:8b','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('common-Bathe-Simi-World-relic',1752614407,1752614407,'qwen3-14b','openrouter/qwen/qwen3-14b:free','qwen/qwen3-14b-04-28',1,'',0,0,0);
INSERT INTO llmmodel VALUES('MAKER-towing-elf-JAR-POKING',1752614407,1752614407,'qwen3-30b','openrouter/qwen/qwen3-30b-a3b:free','qwen/qwen3-30b-a3b-04-28',1,'',0,0,0);
INSERT INTO llmmodel VALUES('rotten-DILL-telly-ELDER-Square',1752614407,1752614407,'qwen3-32b','openrouter/qwen/qwen3-32b:free','qwen/qwen3-32b-04-28',1,'',0,0,0);
INSERT INTO llmmodel VALUES('beast-Women-SON-uppity-POTTS',1752614407,1752614407,'qwerky','openrouter/featherless/qwerky-72b:free','featherless/qwerky-72b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('WING-river-TRAIN-Jeans-POP',1752614407,1752614407,'qwq','openrouter/arliai/qwq-32b-arliai-rpr-v1:free','arliai/qwq-32b-arliai-rpr-v1',1,'',0,0,0);
INSERT INTO llmmodel VALUES('Female-knock-Corner-zombie-Riken',1752614407,1752614407,'reka','openrouter/rekaai/reka-flash-3:free','rekaai/reka-flash-3',1,'',0,0,0);
INSERT INTO llmmodel VALUES('SADDLE-Books-Wall-cherry-nipple',1752614407,1752614407,'rocinante','openrouter/thedrummer/rocinante-12b','thedrummer/rocinante-12b',1,'',1,1,20);
INSERT INTO llmmodel VALUES('SQUASH-ICKY-RELIC-TURN-marine',1752614407,1752614407,'shisa','openrouter/shisa-ai/shisa-v2-llama3.3-70b:free','shisa-ai/shisa-v2-llama3.3-70b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('VAULT-CYRIL-Cosmic-Crook-SHAKY',1752614407,1752614407,'skyfall','openrouter/thedrummer/skyfall-36b-v2','thedrummer/skyfall-36b-v2',1,'',1,0,10);
INSERT INTO llmmodel VALUES('HAMMER-PLUG-Swing-Salad-Kid',1752614407,1752614407,'sorcerer','openrouter/raifle/sorcererlm-8x22b','raifle/sorcererlm-8x22b',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('stuff-crush-Plucky-icky-zany',1752614407,1752614407,'starcannon','openrouter/aetherwiing/mn-starcannon-12b','aetherwiing/mn-starcannon-12b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('rice-charge-mark-summer-Smudge',1752614407,1752614407,'unslop-nemo','openrouter/thedrummer/unslopnemo-12b','thedrummer/unslopnemo-12b',1,'',1,1,20);
COMMIT;
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE llmmodelprice (
	id VARCHAR NOT NULL, 
	created_at INTEGER, 
	updated_at INTEGER, 
	llm_model_id VARCHAR NOT NULL, 
	prompt_price FLOAT NOT NULL, 
	completion_price FLOAT NOT NULL, 
	request_price FLOAT NOT NULL, 
	image_price FLOAT NOT NULL, 
	web_search_price FLOAT NOT NULL, 
	internal_reasoning_price FLOAT NOT NULL, 
	context_length INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(llm_model_id) REFERENCES llmmodel (id)
);
INSERT INTO llmmodelprice VALUES('godwin-shoe-Sign-Warm-EMMET',1752705628,1752705628,'Needy-CLOSE-walk-Half-Pros',3.9999999999999998188e-06,7.9999999999999996378e-06,0.0,0.0,0.0,0.0,131072);
INSERT INTO llmmodelprice VALUES('Print-Grass-Domain-Stream-DEPEND',1752705628,1752705628,'taste-Water-WHARF-street-Toe',6.9999999999999996838e-07,1.3999999999999999367e-06,0.0,0.0,0.0,0.0,131072);
INSERT INTO llmmodelprice VALUES('VENOM-Canvas-FOOL-CHEAT-WRAP',1752705628,1752705628,'bitter-RECENT-Weapon-Limit-DREARY',1.9999999999999999094e-07,1.9999999999999999094e-07,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('TOURED-Murky-FORCE-Gusty-Switch',1752705629,1752705629,'verbs-Jail-Awful-Wing-doll',4.9999999999999997736e-07,9.9999999999999995472e-07,0.0,0.0,0.0,0.0,131072);
INSERT INTO llmmodelprice VALUES('MISCO-Money-VENOM-HUNT-Change',1752705629,1752705629,'spotty-Cobweb-Chief-Beef-Nuclei',7.9999999999999996378e-07,1.1999999999999999457e-06,0.0,0.0,0.0,0.0,16384);
INSERT INTO llmmodelprice VALUES('Divide-FETCH-Demon-Sangre-Jeux',1752705629,1752705629,'beos-Echo-DIRT-liquid-Bronze',3.0000000000000000758e-06,1.5000000000000000379e-05,0.0,0.0047999999999999995795,0.0,0.0,200000);
INSERT INTO llmmodelprice VALUES('uneven-AVOID-Bridge-Uneven-Cook',1752705629,1752705629,'BIKE-Wave-diver-Ting-Engine',3.0000000000000000758e-06,1.5000000000000000379e-05,0.0,0.0047999999999999995795,0.0,0.0,200000);
INSERT INTO llmmodelprice VALUES('Late-ratty-Broome-Guess-feeble',1752705629,1752705629,'DRAWER-AMOUNT-Water-Romano-cloth',1.5000000000000000379e-05,7.4999999999999993429e-05,0.0,0.024000000000000000499,0.0,0.0,200000);
INSERT INTO llmmodelprice VALUES('BOATS-Bloody-bite-aloof-Devil',1752705629,1752705629,'TACIT-Roll-Blaze-PAN-Expect',2.5000000000000002042e-06,1.0000000000000000817e-05,0.0,0.0,0.0,0.0,256000);
INSERT INTO llmmodelprice VALUES('SKINNY-Light-BED-Tired-RATTY',1752705629,1752705629,'mice-corn-ABRUPT-Ask-BEEF',0.0,0.0,0.0,0.0,0.0,0.0,96000);
INSERT INTO llmmodelprice VALUES('BEAR-film-Crazy-spray-Strcpy',1752705629,1752705629,'Cold-HAIR-Warmth-Add-Mask',2.4999999999999998868e-07,8.5000000000000001439e-07,0.0,0.0,0.0,0.0,163840);
INSERT INTO llmmodelprice VALUES('pods-Roll-pencil-guess-rough',1752705629,1752705629,'PRION-SUMMER-blush-Test-Scarf',0.0,0.0,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('RUB-Zip-SINK-Ship-Troll',1752705629,1752705629,'SIDER-Amount-Unit-Debt-CAPPS',0.0,0.0,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('HANDLE-Rough-crack-Knot-Pods',1752705629,1752705629,'VERSE-groan-hydro-CYRIL-CLOSED',5.9999999999999997285e-07,7.9999999999999996378e-07,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('lethal-curl-Speci-Turkey-pack',1752705629,1752705629,'pink-tempo-Part-MARKED-Third',6.5000000000000002354e-07,7.5000000000000001899e-07,0.0,0.0,0.0,0.0,131072);
INSERT INTO llmmodelprice VALUES('DIVIDE-muon-RULES-Spyro-Fancy',1752705629,1752705629,'PURE-Rein-Marine-Frog-annan',6.5000000000000002354e-07,7.5000000000000001899e-07,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('finger-Film-CESSNA-Wizard-BEXLEY',1752705629,1752705629,'love-Look-rejoin-ace-nosy',3.9999999999999998188e-06,6.0000000000000001517e-06,0.0,0.0,0.0,0.0,16384);
INSERT INTO llmmodelprice VALUES('POST-Gala-EXCUSE-Man-land',1752705629,1752705629,'rejoin-FRAIL-Injure-Bow-Tub',7.9999999999999996378e-07,1.1999999999999999457e-06,0.0,0.0,0.0,0.0,4096);
INSERT INTO llmmodelprice VALUES('DENIS-Occur-one-Harrah-Rabid',1752705629,1752705629,'SUIT-tyra-cloth-Luck-Wire',2.9999999999999998642e-07,2.5000000000000002042e-06,0.0,0.0012379999999999999511,0.0,0.0,1048576);
INSERT INTO llmmodelprice VALUES('pods-MURKY-WORM-Things-JAZZY',1752705629,1752705629,'MANDA-Digi-fseek-memory-Dime',1.2500000000000001021e-06,1.0000000000000000817e-05,0.0,0.0051599999999999996563,0.0,0.0,1048576);
INSERT INTO llmmodelprice VALUES('COUGH-Ratty-Hot-Amit-VANISH',1752705629,1752705629,'FIT-Cloth-file-jeans-Hall',0.0,0.0,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('lame-cattle-Geese-Tbsp-earn',1752705629,1752705629,'VESSEL-MUON-Gifted-Mark-BURY',1.9999999999999999094e-06,7.9999999999999996378e-06,0.0,0.0,0.0,0.0,1047576);
INSERT INTO llmmodelprice VALUES('TAX-clammy-SECOND-Handle-Act',1752705629,1752705629,'Quack-shame-Twig-stmt-TOMMY',3.9999999999999998188e-07,1.5999999999999999275e-06,0.0,0.0,0.0,0.0,1047576);
INSERT INTO llmmodelprice VALUES('Rabid-WINING-happy-Tigard-Mean',1752705629,1752705629,'Label-setenv-PLANTS-Equal-ULTIMO',9.9999999999999995472e-08,3.9999999999999998188e-07,0.0,0.0,0.0,0.0,1047576);
INSERT INTO llmmodelprice VALUES('Pickle-fatal-Asce-POTTS-Troup',1752705629,1752705629,'sign-Order-overt-Two-grey',3.0000000000000000758e-06,1.5000000000000000379e-05,0.0,0.0,0.0,0.0,131072);
INSERT INTO llmmodelprice VALUES('GROOVY-Sin-Goff-Sour-ABJECT',1752705629,1752705629,'TIDY-AXONS-Glover-range-seed',2.9999999999999998642e-07,4.9999999999999997736e-07,0.0,0.0,0.0,0.0,131072);
INSERT INTO llmmodelprice VALUES('icann-Scrape-KAPUT-PEAR-HARKIN',1752705629,1752705629,'family-Vast-large-lands-Bell',7.9999999999999996378e-07,3.9999999999999998188e-06,0.0,0.0,0.0,0.0,200000);
INSERT INTO llmmodelprice VALUES('FRIST-Frame-pomp-zip-moteur',1752705629,1752705629,'Loud-atomic-Seed-RELIC-Mighty',0.0,0.0,0.0,0.0,0.0,0.0,131072);
INSERT INTO llmmodelprice VALUES('shiny-pumped-boned-SETTLE-CRABBY',1752705629,1752705629,'toad-blitz-Used-Sin-CRUX',7.9999999999999996378e-07,1.1999999999999999457e-06,0.0,0.0,0.0,0.0,16384);
INSERT INTO llmmodelprice VALUES('deploy-Pure-KNIGHT-MUTE-scrape',1752705629,1752705629,'gaping-TOAD-ULTRA-RHYME-Tall',2.5000000000000002042e-06,1.0000000000000000817e-05,0.0,0.0,0.0,0.0,8000);
INSERT INTO llmmodelprice VALUES('Hover-few-House-Lock-Deploy',1752705629,1752705629,'cleric-Drum-NOUNS-PLANTS-Intend',2.5000000000000002042e-06,1.0000000000000000817e-05,0.0,0.0,0.0,0.0,8000);
INSERT INTO llmmodelprice VALUES('HOUSES-SPY-SALT-DREXEL-Exif',1752705629,1752705629,'angle-slap-Birth-permit-FAGAN',0.0,0.0,0.0,0.0,0.0,0.0,131072);
INSERT INTO llmmodelprice VALUES('jewel-Color-peck-Eerie-Old',1752705629,1752705629,'SKIRT-pasted-wreck-Food-REEF',0.0,0.0,0.0,0.0,0.0,0.0,131072);
INSERT INTO llmmodelprice VALUES('PAPER-Gabor-zip-haunt-nerdy',1752705629,1752705629,'HYDRO-DAMAGE-EFFECT-Tray-dead',1.4999999999999999321e-07,1.4999999999999999321e-07,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('DERRY-Phone-Wrench-Kids-Rain',1752705629,1752705629,'MILKY-Add-Jeux-HANDS-stay',1.4999999999999999321e-07,5.9999999999999997285e-07,0.0,0.00066839999999999998372,0.0,0.0,1048576);
INSERT INTO llmmodelprice VALUES('Drawer-Slap-Crash-Nsta-Pixma',1752705629,1752705629,'Paper-border-Slim-Kettle-array',8.0000000000000001674e-08,2.9999999999999998642e-07,0.0,0.0,0.0,0.0,1048576);
INSERT INTO llmmodelprice VALUES('kidman-boas-Muscle-Intend-basket',1752705629,1752705629,'deer-Serve-WITTY-parcel-Launch',1.9999999999999999094e-06,5.0000000000000004085e-06,0.0,0.0,0.0,0.0,40960);
INSERT INTO llmmodelprice VALUES('DONKEY-Ical-EVITE-Admire-Crayon',1752705629,1752705629,'land-LIVE-Tacit-BRIGHT-Rebel',9.9999999999999995472e-08,2.9999999999999998642e-07,0.0,0.0,0.0,0.0,40960);
INSERT INTO llmmodelprice VALUES('TEMPER-OTTER-Peace-motel-COOKE',1752705629,1752705629,'Meat-DUBLIN-nerdy-Nerdy-narrow',2.5000000000000002042e-06,3.0000000000000000758e-06,0.0,0.0,0.0,0.0,16384);
INSERT INTO llmmodelprice VALUES('Jaded-SIDING-spooky-Wharf-Zipper',1752705629,1752705629,'mori-Boot-SORTS-burch-EMMET',7.9999999999999996378e-07,7.9999999999999996378e-07,0.0,0.0,0.0,0.0,4096);
INSERT INTO llmmodelprice VALUES('jaguar-WINING-Vulgar-BEEF-Vinny',1752705629,1752705629,'expres-Pixie-MOVING-Visit-EARTHY',2.9999999999999998642e-07,1.6500000000000000842e-06,0.0,0.0,0.0,0.0,1000000);
INSERT INTO llmmodelprice VALUES('jtag-Priest-things-Third-LANGE',1752705629,1752705629,'lace-Array-airing-Show-COOING',0.0,0.0,0.0,0.0,0.0,0.0,128000);
INSERT INTO llmmodelprice VALUES('LURES-frost-Superb-Onions-cruel',1752705629,1752705629,'PLACE-Bang-Travel-Earthy-tender',1.9999999999999999094e-06,7.9999999999999996378e-06,0.0,0.001529999999999999893,0.0,0.0,200000);
INSERT INTO llmmodelprice VALUES('Windy-thank-church-Miko-Amount',1752705629,1752705629,'MICE-NIPPLE-Lumpy-Admit-Club',1.100000000000000056e-06,4.4000000000000002242e-06,0.0,0.0,0.0,0.0,200000);
INSERT INTO llmmodelprice VALUES('storm-freeze-JADED-YARD-SIGHS',1752705629,1752705629,'wound-CRAVEN-Rock-HELM-Fuzzy',1.100000000000000056e-06,4.4000000000000002242e-06,0.0,0.00084150000000000001708,0.0,0.0,200000);
INSERT INTO llmmodelprice VALUES('shew-Grass-Lett-Shaft-Kettle',1752705629,1752705629,'occur-Word-Gabby-HELP-slow',1.100000000000000056e-06,4.4000000000000002242e-06,0.0,0.00084150000000000001708,0.0,0.0,200000);
INSERT INTO llmmodelprice VALUES('lick-moteur-LUCKY-fierce-MIDDLE',1752705629,1752705629,'gate-Errata-dohc-ABRUPT-Bite',1.4999999999999999321e-07,5.9999999999999997285e-07,0.0,0.00021699999999999998912,0.0,0.0,128000);
INSERT INTO llmmodelprice VALUES('SULKY-HUSKY-Nerdy-Gabor-Family',1752705629,1752705629,'bead-Kemp-AZTEC-Slow-stone',1.5999999999999999275e-06,6.3999999999999997103e-06,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('guide-fluffy-dead-Floor-windy',1752705629,1752705629,'common-Bathe-Simi-World-relic',0.0,0.0,0.0,0.0,0.0,0.0,40960);
INSERT INTO llmmodelprice VALUES('KNIGHT-Salad-Fiend-Dohc-Unload',1752705629,1752705629,'MAKER-towing-elf-JAR-POKING',0.0,0.0,0.0,0.0,0.0,0.0,40960);
INSERT INTO llmmodelprice VALUES('MOVING-Chuan-front-Hope-Hervey',1752705629,1752705629,'rotten-DILL-telly-ELDER-Square',0.0,0.0,0.0,0.0,0.0,0.0,40960);
INSERT INTO llmmodelprice VALUES('Attach-live-Trucks-Fail-Stamp',1752705629,1752705629,'beast-Women-SON-uppity-POTTS',0.0,0.0,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('Wry-SPELL-TIGARD-Angle-Large',1752705629,1752705629,'WING-river-TRAIN-Jeans-POP',0.0,0.0,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('PORTER-Pine-Mossy-TENDER-SACHS',1752705629,1752705629,'Female-knock-Corner-zombie-Riken',0.0,0.0,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('PAPER-SPROUT-pinch-PEEL-Pink',1752705629,1752705629,'SADDLE-Books-Wall-cherry-nipple',1.9999999999999999094e-07,4.9999999999999997736e-07,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('CHUNKY-Bottle-parka-Print-HUM',1752705629,1752705629,'SQUASH-ICKY-RELIC-TURN-marine',0.0,0.0,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('WINDY-Uppity-MOLDY-SEAT-clever',1752705629,1752705629,'VAULT-CYRIL-Cosmic-Crook-SHAKY',3.9999999999999998188e-07,6.9999999999999996838e-07,0.0,0.0,0.0,0.0,32768);
INSERT INTO llmmodelprice VALUES('Odd-Flavor-Innate-ROCK-SLIM',1752705629,1752705629,'HAMMER-PLUG-Swing-Salad-Kid',4.500000000000000114e-06,4.500000000000000114e-06,0.0,0.0,0.0,0.0,16000);
INSERT INTO llmmodelprice VALUES('Walk-Eggs-Remedy-ERRATA-SCALE',1752705629,1752705629,'stuff-crush-Plucky-icky-zany',7.9999999999999996378e-07,1.1999999999999999457e-06,0.0,0.0,0.0,0.0,16384);
INSERT INTO llmmodelprice VALUES('Brave-Ray-RIDDLE-adder-Normal',1752705629,1752705629,'rice-charge-mark-summer-Smudge',3.9999999999999998188e-07,3.9999999999999998188e-07,0.0,0.0,0.0,0.0,32768);
COMMIT;
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE llmmodelstats (
	id VARCHAR NOT NULL, 
	created_at INTEGER, 
	updated_at INTEGER, 
	llm_model_id INTEGER NOT NULL, 
	eval_type VARCHAR NOT NULL, 
	run_id VARCHAR, 
	duration_ms INTEGER, 
	success BOOLEAN, 
	error_message VARCHAR, 
	timestamp INTEGER, 
	extra VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(llm_model_id) REFERENCES llmmodel (id)
);
COMMIT;
